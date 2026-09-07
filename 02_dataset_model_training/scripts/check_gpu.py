import torch

print("=" * 50)
print("GPU / PyTorch Check")
print("=" * 50)

print(f"PyTorch version : {torch.__version__}")
print(f"CUDA available  : {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU count       : {torch.cuda.device_count()}")

    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}          : {torch.cuda.get_device_name(i)}")

    print(f"CUDA version    : {torch.version.cuda}")
else:
    print("\nWARNING: CUDA GPU is NOT available.")
    print("Training will use CPU, which is not recommended.")

print("=" * 50)