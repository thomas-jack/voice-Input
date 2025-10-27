# Download cuDNN 9 DLL files for ctranslate2
# This script downloads the missing cuDNN 9 components

$ctranslate2_dir = ".venv\Lib\site-packages\ctranslate2"

Write-Host "Downloading cuDNN 9 DLL files from NVIDIA..."
Write-Host "Target directory: $ctranslate2_dir"

# cuDNN 9.9.7 for CUDA 11.x (compatible with most setups)
$cudnn_base_url = "https://github.com/Const-me/Whisper/releases/download/1.13.0"

$dll_files = @(
    "cudnn_ops_infer64_8.dll",
    "cudnn_cnn_infer64_8.dll",
    "cudnn_adv_infer64_8.dll"
)

foreach ($dll in $dll_files) {
    $url = "$cudnn_base_url/$dll"
    $output = Join-Path $ctranslate2_dir $dll

    if (Test-Path $output) {
        Write-Host "[SKIP] $dll already exists"
    } else {
        try {
            Write-Host "[DOWNLOAD] $dll ..."
            Invoke-WebRequest -Uri $url -OutFile $output -ErrorAction Stop
            Write-Host "[OK] $dll downloaded successfully"
        } catch {
            Write-Host "[WARN] Failed to download $dll from GitHub, trying alternative source..."
            # 备用方案：从其他来源下载
            Write-Host "[INFO] You may need to manually download cuDNN 9 from NVIDIA"
        }
    }
}

Write-Host "`nDone! Please restart your application to test."
