from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import os
from datetime import datetime

app = Flask(__name__)
# 创建文件保存路径
output_dir = os.path.join(app.root_path, 'static')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


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

@app.route('/polygons', methods=['POST'])
def receive_polygons():
    data = request.json  # 获取前端发送的 JSON 数据
    print('Received data:', data)

    # 创建空白黑色图像，设置图像尺寸
    image_height, image_width = 480, 640  # 根据前端 canvas 的尺寸
    binary_image = np.zeros((image_height, image_width), dtype=np.uint8)

    download_links = []  # 用于存储文件的下载地址
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # 获取当前时间的时间戳
    all_coordinates_str = ""  # 用于保存所有多边形的坐标

    # 处理接收到的多边形数据
    for i, polygon_data in enumerate(data):
        points = polygon_data['points']
        # 转换点坐标为整数，并相对于图像尺寸进行缩放
        polygon_points = np.array([[int(float(p['x']) * image_width), int(float(p['y']) * image_height)] for p in points])
        polygon_points_f16 = ([[p['x'], p['y']] for p in points])

        # 填充多边形区域为白色
        cv2.fillPoly(binary_image, [polygon_points], 255)

        # 为每个多边形生成一行坐标字符串
        class_index = 0  # 可以根据需要修改 class-index
        coordinates_str = f"{class_index} " + " ".join([f"{x} {y}" for x, y in polygon_points_f16])
        all_coordinates_str += coordinates_str + "\n"  # 将多边形坐标添加到总字符串中

    # 保存所有多边形的坐标到一个文本文件，使用时间戳防止重名
    txt_file_name = f'polygons_{timestamp}.txt'
    txt_file_path = os.path.join(output_dir, txt_file_name)
    with open(txt_file_path, 'w') as f:
        f.write(all_coordinates_str)
    
    # 添加 txt 文件的下载链接
    download_links.append(f'/static/{txt_file_name}')

    # 保存二值化图像，使用时间戳防止重名
    image_file_name = f'binary_image_{timestamp}.png'
    image_path = os.path.join(output_dir, image_file_name)
    cv2.imwrite(image_path, binary_image)
    download_links.append(f'/static/{image_file_name}')  # 添加图像的下载链接

    # 返回响应，包含文件的下载链接
    return jsonify({'status': 'success', 'message': 'Files generated successfully!', 'download_links': download_links})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
