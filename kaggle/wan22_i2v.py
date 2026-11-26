# Kaggle script kernel: Wan 2.2 TI2V-5B image-to-video for the moving shots (ticket 07).
#
# The pipeline (pipeline/stages/moving.py via KaggleJobs) prepends one line, `JOB = {...}`:
#   JOB["items"]: [{"id", "image", "prompt", "negative_prompt", "seed", "width", "height",
#                   "num_frames", "steps", "guidance", "flow_shift", "fps"}]
#   JOB["files"]: {file name: base64}  (the keyframes, already resized to width x height)
#   JOB["model"], JOB["diffusers"]: the HF repo and the diffusers pip spec
# Each clip is saved to /kaggle/working as soon as it finishes, and results.json is rewritten
# after every item, so a session that dies part-way keeps the clips it finished.
# Not run yet at the time of writing: see FAILURES.md for what happened on Kaggle.

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

    import numpy as np
    import torch
    from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanImageToVideoPipeline, WanTransformer3DModel
    from diffusers.hooks import apply_group_offloading
    from diffusers.utils import export_to_video, load_image
    from transformers import UMT5EncoderModel

    major, _ = torch.cuda.get_device_capability()
    # T4 and P100 have no native bf16: the transformer runs in fp16 there. The text encoder stays
    # bf16 (UMT5 overflows to NaN in fp16) and the VAE fp32 (the model card's advice).
    dtype = torch.bfloat16 if major >= 8 else torch.float16
    results["_device"] = {"gpu": torch.cuda.get_device_name(0), "transformer_dtype": str(dtype)}
    save()

    model = JOB["model"]
    vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
    text_encoder = UMT5EncoderModel.from_pretrained(model, subfolder="text_encoder", torch_dtype=torch.bfloat16)
    transformer = WanTransformer3DModel.from_pretrained(model, subfolder="transformer", torch_dtype=dtype)
    # First run: model CPU offload put the whole 10 GB transformer on the 14.5 GB T4 and ran out of
    # memory in its feed-forward layers. Group offloading streams it from CPU memory layer by layer
    # (the diffusers docs' recipe for Wan in ~13 GB); the VAE decodes in tiles.
    cuda, cpu = torch.device("cuda"), torch.device("cpu")
    apply_group_offloading(text_encoder, onload_device=cuda, offload_device=cpu, offload_type="block_level",
                           num_blocks_per_group=4)
    transformer.enable_group_offload(onload_device=cuda, offload_device=cpu, offload_type="leaf_level", use_stream=True)
    pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, text_encoder=text_encoder, transformer=transformer,
                                                   torch_dtype=dtype)
    pipe.to("cuda")
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
                prompt=item["prompt"],
                negative_prompt=item["negative_prompt"],
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
