# Kaggle script kernel: Wan 2.2 TI2V-5B image-to-video for the moving shots (ticket 07).
#
# The pipeline (pipeline/stages/moving.py via KaggleJobs) prepends one line, `JOB = {...}`:
#   JOB["items"]: [{"id", "image", "prompt", "negative_prompt", "seed", "width", "height",
#                   "num_frames", "steps", "guidance", "flow_shift", "fps"}]
#   JOB["files"]: {file name: base64}  (the keyframes, already resized to width x height)
#   JOB["model"], JOB["diffusers"]: the HF repo and the diffusers pip spec
# Each clip is saved to /kaggle/working as soon as it finishes, and results.json is rewritten
# after every item, so a session that dies part-way keeps the clips it finished.
# Attempts 1 and 2 ran out of memory on a Kaggle T4; this is attempt 3 (FAILURES.md F10).

import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

OUT = Path("/kaggle/working")
INPUTS = Path("/tmp/inputs")
results = {}


def save():
    (OUT / "results.json").write_text(json.dumps(results, indent=1))


def main():
    INPUTS.mkdir(parents=True, exist_ok=True)
    for name, data in JOB["files"].items():
        (INPUTS / name).write_bytes(base64.b64decode(data))
    os.environ.setdefault("HF_HOME", "/tmp/hf")  # /kaggle/working is capped at 20 GB; weights are ~25 GB
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    started = time.time()
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", JOB["diffusers"], "ftfy", "imageio",
                    "imageio-ffmpeg"], check=True)

    import gc

    import numpy as np
    import torch
    from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image
    from transformers import UMT5EncoderModel

    major, _ = torch.cuda.get_device_capability()
    # T4 and P100 have no native bf16: the transformer runs in fp16 there. The text encoder stays
    # bf16 (UMT5 overflows to NaN in fp16) and the VAE fp32 (the model card's advice).
    dtype = torch.bfloat16 if major >= 8 else torch.float16
    results["_device"] = {"gpu": torch.cuda.get_device_name(0), "transformer_dtype": str(dtype)}
    save()
    model = JOB["model"]

    # Attempt 3 (FAILURES.md F10): never hold the 11 GB text encoder and the 10 GB transformer at once.
    # Step 1: encode every prompt with the text encoder alone on the GPU, keep the embeddings, free it.
    text_encoder = UMT5EncoderModel.from_pretrained(model, subfolder="text_encoder", torch_dtype=torch.bfloat16)
    encoder = WanImageToVideoPipeline.from_pretrained(model, text_encoder=text_encoder, transformer=None, vae=None,
                                                      torch_dtype=torch.bfloat16).to("cuda")
    embeds = {}
    with torch.no_grad():
        for item in JOB["items"]:
            positive, negative = encoder.encode_prompt(prompt=item["prompt"], negative_prompt=item["negative_prompt"],
                                                       do_classifier_free_guidance=True, device="cuda")
            embeds[item["id"]] = (positive.to("cpu", dtype), negative.to("cpu", dtype))
    del encoder, text_encoder
    gc.collect()
    torch.cuda.empty_cache()
    results["_encode"] = {"seconds": round(time.time() - started, 1)}
    save()

    # Step 2: the transformer and VAE only, with model CPU offload (attempt 1 failed at 121 frames; now 81).
    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, text_encoder=None, tokenizer=None, torch_dtype=dtype)
    pipe.enable_model_cpu_offload()
    try:
        pipe.vae.enable_tiling()
    except Exception:
        traceback.print_exc()
    results["_load"] = {"seconds": round(time.time() - started, 1)}
    save()

    for item in JOB["items"]:
        t = time.time()
        try:
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=item["flow_shift"])
            frames = pipe(
                image=load_image(str(INPUTS / item["image"])),
                prompt_embeds=embeds[item["id"]][0].to("cuda"),
                negative_prompt_embeds=embeds[item["id"]][1].to("cuda"),
                height=item["height"],
                width=item["width"],
                num_frames=item["num_frames"],
                guidance_scale=item["guidance"],
                num_inference_steps=item["steps"],
                generator=torch.Generator("cpu").manual_seed(item["seed"]),
            ).frames[0]
            if float(np.asarray(frames).mean()) < 0.01:
                raise RuntimeError("all-black frames (fp16 overflow?)")
            name = f"{item['id']}.mp4"
            export_to_video(frames, str(OUT / name), fps=item["fps"])
            results[item["id"]] = {"file": name, "seconds": round(time.time() - t, 1)}
        except Exception as e:
            traceback.print_exc()
            results[item["id"]] = {"error": f"{type(e).__name__}: {e}"[:500], "seconds": round(time.time() - t, 1)}
            frames = None
            torch.cuda.empty_cache()  # first run: one out-of-memory clip left the GPU full for the next ones
        save()


try:
    main()
except Exception as e:
    traceback.print_exc()
    results["_job"] = {"error": f"{type(e).__name__}: {e}"[:500]}
    save()
    raise
