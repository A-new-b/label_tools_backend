import subprocess

def avi_to_mp4(input_file, output_file):
    try:
        # 使用 ffmpeg 将 AVI 转换为 MP4
        subprocess.run(['ffmpeg', '-i', input_file, output_file], check=True)
        print(f"Conversion successful! {input_file} has been converted to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

# 示例使用
input_avi = '新相机-SF6-2.avi'
output_mp4 = 'SF6-2.mp4'
avi_to_mp4(input_avi, output_mp4)
