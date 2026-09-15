"""Report the available PyTorch inference/training device."""

import argparse


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    import torch

    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            print(f"GPU {index}: {torch.cuda.get_device_name(index)}")
        print(f"CUDA version: {torch.version.cuda}")
    else:
        print("Inference and training will use CPU.")


if __name__ == "__main__":
    main()
