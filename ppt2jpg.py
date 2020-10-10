import win32com
import win32com.client
import sys
import os
from PIL import Image

def output_file(ppt_path):
    return ppt_path.rsplit('.')[0]

def generate_long_image(output_path):
    picture_path = output_path
    last_dir = os.path.dirname(picture_path)  # 上一级文件目录

    # 获取单个图片
    ims = [Image.open(os.path.join(picture_path, fn)) for fn in os.listdir(picture_path) if fn.endswith('.jpg')]
    width, height = ims[0].size  # 取第一个图片尺寸
    # print(width, height)
    for im in ims:
        im.thumbnail((width//2, height//2))
    width, height = ims[0].size
    # print(width, height)
    long_canvas = Image.new(ims[0].mode, (width, height * len(ims)))  # 创建同宽，n高的白图片

    # 拼接图片
    for i, image in enumerate(ims):
        long_canvas.paste(image, box=(0, i * height))
    long_canvas.save(os.path.join(last_dir, 'long-image.png'))  # 保存长图

def ppt2png(ppt_path, long_sign: str):
    """
    ppt 转 png 方法
    :param ppt_path: ppt 文件的绝对路径
    :param long_sign: 是否需要转为生成长图的标识
    :return:
    """
    if os.path.exists(ppt_path):
        output_path = output_file(ppt_path)  # 判断文件是否存在

        ppt_app = win32com.client.Dispatch('PowerPoint.Application')
        ppt = ppt_app.Presentations.Open(ppt_path)  # 打开 ppt
        ppt.SaveAs(output_path+".jpg", 17)  # 17数字是转为 ppt 转为图片
        ppt.Close()  # 关闭资源，退出

        if 'Y' == long_sign.upper():
            generate_long_image(output_path)  # 合并生成长图

    else:
        raise Exception('请检查文件是否存在！\n')

ppt_path = os.path.join(os.path.dirname(__file__), "1.pptx")
from pathlib import Path
ppt_path = Path(ppt_path).as_posix()
print(ppt_path)
ppt2png(ppt_path, "y")