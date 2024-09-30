from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64

app = Flask(__name__)

def decode_image(base64_str):
    # 去除 'data:image/png;base64,' 或其他类似前缀
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    # 解码 base64 字符串为图像
    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

def encode_image(image):
    # 将图像编码为 base64 字符串
    _, buffer = cv2.imencode('.png', image)
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return f'data:image/png;base64,{base64_str}'

@app.route('/image_diff', methods=['POST'])
def image_diff():
    data = request.get_json()

    # 获取并解码两张图片
    img1_base64 = data.get('image1')
    img2_base64 = data.get('image2')
    threshold = data.get('threshold', 0)  # 默认阈值为 0

    if not img1_base64 or not img2_base64:
        return jsonify({'error': 'Missing image data'}), 400

    try:
        img1 = decode_image(img1_base64)
        img2 = decode_image(img2_base64)

        # 检查两张图片尺寸是否相同
        if img1.shape != img2.shape:
            return jsonify({'error': 'Images must have the same dimensions'}), 400

        # 计算图像差分
        diff = cv2.absdiff(img1, img2)

        # 应用阈值
        _, thresholded_diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # 将差分图像编码为 base64
        diff_base64 = encode_image(thresholded_diff)

        return jsonify({'diff_image': diff_base64})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
