#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@date: 2021-01-31
@author: Shell.Xu
@copyright: 2021, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
@comment:
add watermark to picture.
为图片增加水印。
python3 watermark.py -m watermark [-o output file] [-f font] [-s size] [src file]
'''
import sys
import logging
import argparse
from os import path

from PIL import Image, ImageDraw, ImageFont, ImageOps


logger = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


parser = argparse.ArgumentParser()
parser.add_argument('--watermark', '-m', help='watermark to write')
parser.add_argument('--font', '-f', help='path of font file.')
parser.add_argument('--fontsize', '-s', type=int, default=64, help='size of font, 64 by default.')
parser.add_argument('--alpha', '-a', type=int, default=50, help='alpha of font, 50 by default.')
parser.add_argument('--rotate', '-r', type=int, default=30, help='angle of rotation, 30 by default.')
parser.add_argument('--xdensity', '-x', type=float, default=1.5, help='density in X, 1.5 by default.')
parser.add_argument('--ydensity', '-y', type=float, default=1.5, help='density in Y, 1.5 by default.')
parser.add_argument('--output', '-o', help='output file. write back to input if not setting.')
parser.add_argument('rest', nargs='*', type=str)
args = parser.parse_args()

if not args.font:
    args.font = "/System/Library/Fonts/STHeiti Light.ttc"
    if not path.isfile(args.font):
        args.font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def watermark(src):
    img = Image.open(src).convert("RGBA")
    width, height = img.size

    font = ImageFont.truetype(args.font, args.fontsize)

    draw = ImageDraw.Draw(img)
    txt_width, txt_height = draw.textsize(args.watermark, font)

    txt = Image.new('RGBA', (txt_width, txt_height), (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    draw.text((0,0), args.watermark, fill=(0,0,0,args.alpha), font=font)
    txt = txt.rotate(args.rotate, expand=1)
    txt_width, txt_height = txt.size

    for i in range(int(width/txt_width+1)):
        for j in range(int(height/txt_height+1)):
            x = int(args.xdensity*i*txt_width)
            y = int(args.ydensity*j*txt_height)
            img.alpha_composite(txt, dest=(x, y))

    dst = args.output or src
    img.convert('RGB').save(dst)  # quality=75


def main():
    watermark(args.rest[0])


if __name__ == '__main__':
    main()
