import argparse
import os
import subprocess
import sys
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
AIONER_SRC_DIR = PROJECT_ROOT / "NLPv2.4" / "AIONER-main" / "src"
AIONER_ROOT = AIONER_SRC_DIR.parent
DEFAULT_INPUT_DIR = SCRIPT_DIR / "output"
DEFAULT_INPUT_FILE = DEFAULT_INPUT_DIR / "pubmed_phosphoryl_pubtator.txt"
DEFAULT_STAGED_INPUT_DIR = SCRIPT_DIR / "output" / "aioner_input"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output" / "aioner_output"
DEFAULT_MODEL = AIONER_ROOT / "pretrained_models" / "AIONER" / "Bioformer-softmax-AIONER.h5"
DEFAULT_VOCAB = AIONER_ROOT / "vocab" / "AIO_label.vocab"


def to_aioner_relative(path):
    return Path(os.path.relpath(str(Path(path).resolve()), str(AIONER_SRC_DIR))).as_posix()


def main():
    parser = argparse.ArgumentParser(
        description="Run the existing NLPv2.4 AIONER model from new_training_data."
    )
    parser.add_argument(
        "--python",
        dest="python_exe",
        default=sys.executable,
        help="Python executable for the AIONER environment.",
    )
    parser.add_argument(
        "--input-file",
        default=str(DEFAULT_INPUT_FILE),
        help="PubTator input file generated in trainingdata.",
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_STAGED_INPUT_DIR),
        help="Directory containing only the staged AIONER input files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for AIONER outputs.",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
        help="AIONER model file from NLPv2.4.",
    )
    parser.add_argument(
        "--vocab",
        default=str(DEFAULT_VOCAB),
        help="AIONER vocab file from NLPv2.4.",
    )
    parser.add_argument(
        "--entity",
        default="ALL",
        help="Entity type for AIONER_Run.py.",
    )
    args = parser.parse_args()

    input_file = Path(args.input_file).resolve()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    model_file = Path(args.model).resolve()
    vocab_file = Path(args.vocab).resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Missing input file: {input_file}")

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    staged_input = input_dir / input_file.name
    for existing in input_dir.iterdir():
        if existing.is_file():
            existing.unlink()
    if staged_input != input_file:
        shutil.copyfile(str(input_file), str(staged_input))

    model_arg = to_aioner_relative(model_file)
    vocab_arg = to_aioner_relative(vocab_file)
    input_arg = input_dir.as_posix()
    output_arg = output_dir.as_posix()

    command = [
        args.python_exe,
        "AIONER_Run.py",
        "-i",
        input_arg,
        "-m",
        model_arg,
        "-v",
        vocab_arg,
        "-e",
        args.entity,
        "-o",
        output_arg,
    ]

    print("Running:", " ".join(command))
    subprocess.run(command, check=True, cwd=str(AIONER_SRC_DIR))


if __name__ == "__main__":
    main()
