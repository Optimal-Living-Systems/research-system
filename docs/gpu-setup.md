# GPU Setup Guide

## Overview

GPU servers are needed for two tasks:
1. **Fine-tuning** (one-time, ~20 hours on A100)
2. **Inference** (ongoing, pay-per-use)

## Fine-Tuning: RunPod

### Why RunPod
- On-demand GPU rental, pay by the hour
- Good API for automation (Kestra integration)
- A100 80GB available at ~$2-3/hr
- Community Cloud option for lower prices

### Step-by-Step Setup

1. Create account at https://www.runpod.io
2. Add payment method
3. Go to **Pods → Deploy**
4. Select GPU: **A100 80GB SXM** (or A100 80GB PCIe)
5. Select template: **RunPod Pytorch 2.x** 
6. Set volume size: **100GB** (for model + data)
7. Deploy and note the SSH connection details

### On the GPU Server

```bash
# Install Unsloth (fast QLoRA training)
pip install unsloth

# Install additional dependencies
pip install datasets transformers trl accelerate bitsandbytes

# Upload your training data (from your local machine or Kestra)
# scp training_data.jsonl root@your-pod-ip:/workspace/

# Run training (see scripts/train.py for full script)
python /workspace/train.py
```

### After Training

```bash
# Download the LoRA adapter weights
# scp -r root@your-pod-ip:/workspace/output/lora-adapter ./

# Stop the pod to stop billing
# Use RunPod UI or API to terminate
```

### Estimated Costs
- Training run: $40-80 (20 hours × $2-4/hr)
- You may need 2-3 runs to iterate: budget $120-240 total

## Inference: Modal

### Why Modal
- Serverless: scales to zero when not in use
- Pay per second of compute
- Easy Python SDK
- No server management

### Setup

```bash
pip install modal
modal setup  # Follow auth flow
```

### Deploy Model

```python
# See scripts/deploy_modal.py for full deployment script
# Modal will automatically provision GPU when requests come in
# and scale to zero when idle
```

### Estimated Costs
- Light usage (10-50 queries/day): $30-50/month
- Heavy usage (100-500 queries/day): $100-200/month
- No usage: $0/month (scales to zero)

## Alternative: Together.ai Fine-Tuning API

If you want zero GPU management:

1. Create account at https://api.together.ai
2. Upload training data via API
3. Start fine-tuning job via API
4. They handle all GPU provisioning
5. Model hosted on their infrastructure for inference

Pros: No GPU management at all
Cons: Less control, vendor dependency, higher per-token cost
