# Kaggle script kernel: ACE-Step 1.5 score candidates (ticket 06).
#
# The pipeline (pipeline/stages/music.py via KaggleJobs) prepends one line, `JOB = {...}`:
#   JOB["items"]: [{"id", "caption", "duration_s", "seed", "steps", "shift"}]
#   JOB["repo"], JOB["config"], JOB["lm"]: the ACE-Step git repo, DiT config and planner LM
# ACE-Step 1.5 is installed the documented way (git clone + uv sync) into its own environment,
# and generation runs there as a child script. Each candidate is copied to /kaggle/working as
# soon as it is rendered, and results.json is rewritten after every candidate.
# Not run yet at the time of writing: see FAILURES.md for what happened on Kaggle.

import shutil
import subprocess
import sys
import traceback
from pathlib import Path

OUT = Path("/kaggle/working")
ACE = Path("/tmp/ACE-Step-1.5")

CHILD = r'''
import dataclasses, json, shutil, sys, time, traceback
from pathlib import Path
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationConfig, GenerationParams, generate_music

job = json.loads(Path(sys.argv[1]).read_text())
out = Path("/kaggle/working")
results_path = out / "results.json"
results = json.loads(results_path.read_text()) if results_path.exists() else {}

def save():
    results_path.write_text(json.dumps(results, indent=1))

def only_known(cls, **kwargs):
    # Keep the keyword arguments this ACE-Step version accepts (the docs and the code may drift).
    names = {f.name for f in dataclasses.fields(cls)} if dataclasses.is_dataclass(cls) else set(kwargs)
    return cls(**{k: v for k, v in kwargs.items() if k in names})

dit = AceStepHandler()
dit.initialize_service(project_root=job["root"], config_path=job["config"], device="cuda")
llm = LLMHandler()
try:  # the planner LM is not used (thinking=False), but generate_music takes a handler
    llm.initialize(checkpoint_dir=job["root"] + "/checkpoints", lm_model_path=job["lm"], backend="pt", device="cuda")
except Exception:
    traceback.print_exc()

for item in job["items"]:
    t = time.time()
    try:
        params = only_known(GenerationParams, task_type="text2music", caption=item["caption"],
                            lyrics="[Instrumental]", instrumental=True, duration=item["duration_s"],
                            inference_steps=item["steps"], shift=item["shift"], seed=item["seed"], thinking=False)
        config = only_known(GenerationConfig, batch_size=1, use_random_seed=False, audio_format="wav")
        res = generate_music(dit, llm, params, config, save_dir="/tmp/ace-out")
        if not res.success:
            raise RuntimeError(res.error or res.status_message)
        name = item["id"] + ".wav"
        shutil.copy(res.audios[0]["path"], out / name)
        results[item["id"]] = {"file": name, "seconds": round(time.time() - t, 1)}
    except Exception as e:
        traceback.print_exc()
        results[item["id"]] = {"error": f"{type(e).__name__}: {e}"[:500], "seconds": round(time.time() - t, 1)}
    save()
'''


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, **kw)


def main():
    run([sys.executable, "-m", "pip", "install", "-q", "uv"])
    run(["git", "clone", "--depth", "1", JOB["repo"], str(ACE)])
    run(["uv", "sync"], cwd=ACE)
    run(["uv", "run", "acestep-download"], cwd=ACE)
    (ACE / "job_child.py").write_text(CHILD)
    (ACE / "job.json").write_text(json.dumps({**JOB, "root": str(ACE)}))
    run(["uv", "run", "python", "job_child.py", "job.json"], cwd=ACE)


try:
    main()
except Exception as e:
    traceback.print_exc()
    path = OUT / "results.json"
    results = json.loads(path.read_text()) if path.exists() else {}
    results["_job"] = {"error": f"{type(e).__name__}: {e}"[:500]}
    path.write_text(json.dumps(results, indent=1))
    raise
finally:
    shutil.rmtree("/tmp/ace-out", ignore_errors=True)
