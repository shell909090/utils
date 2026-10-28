#!/bin/bash

# 检查参数
if [ "$#" -ne 2 ]; then
    echo "使用方法: $0 <原始视频> <目标图片文件名>"
    echo "示例: $0 input.mp4 IMG_20260114_0001.jpg"
    exit 1
fi

SRC_VIDEO=$1
TARGET_IMAGE=$2

# 临时文件名定义
TEMP_VIDEO="temp_native_video.mp4"
TEMP_XMP="temp_motion.xmp"

echo "--- [1/5] 正在重编码视频 (修正旋转 & 适配小米参数) ---"
# 物理旋转像素，抹除旋转标记，对齐 H.264 High@L4.0
ffmpeg -i "$SRC_VIDEO" \
    -vf "format=yuv420p" \
    -c:v libx264 -profile:v high -level 4.0 -crf 20 \
    -c:a aac -b:a 128k \
    -movflags +faststart \
    -metadata:s:v:0 rotate=0 \
    -y "$TEMP_VIDEO"

if [ $? -ne 0 ]; then echo "视频重编码失败"; exit 1; fi

echo "--- [2/5] 提取视频第一帧作为封面 ---"
ffmpeg -i "$TEMP_VIDEO" -frames:v 1 -q:v 2 -y "$TARGET_IMAGE"

# 获取视频精确字节数
VIDEO_SIZE=$(stat -f%z "$TEMP_VIDEO")

echo "--- [3/5] 生成原生 XML 元数据 (Length: $VIDEO_SIZE) ---"
# 使用 cat <<EOF 直接生成 XML 字符串并填入变量
cat <<EOF > "$TEMP_XMP"
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.1.0-jc003">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:GCamera="http://ns.google.com/photos/1.0/camera/"
        xmlns:Container="http://ns.google.com/photos/1.0/container/"
        xmlns:Item="http://ns.google.com/photos/1.0/container/item/"
      GCamera:MotionPhoto="1"
      GCamera:MotionPhotoVersion="1"
      GCamera:MotionPhotoPresentationTimestampUs="0">
      <Container:Directory>
        <rdf:Seq>
          <rdf:li rdf:parseType="Resource">
            <Container:Item Item:Mime="image/jpeg" Item:Semantic="Primary"/>
          </rdf:li>
          <rdf:li rdf:parseType="Resource">
            <Container:Item Item:Mime="video/mp4" Item:Semantic="MotionPhoto" Item:Length="$VIDEO_SIZE" Item:Padding="0"/>
          </rdf:li>
        </rdf:Seq>
      </Container:Directory>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
EOF

echo "--- [4/5] 注入 XMP 元数据 ---"
# 使用你发现的引号包裹技巧，防止 Shell 重定向干扰
exiftool -all= -xmp"<=$TEMP_XMP" "$TARGET_IMAGE"

echo "--- [5/5] 物理合并视频流 ---"
# 直接将视频流追加到图片末尾
cat "$TEMP_VIDEO" >> "$TARGET_IMAGE"

# 清理现场
rm "$TEMP_VIDEO" "$TEMP_XMP" "${TARGET_IMAGE}_original" 2>/dev/null

echo "-----------------------------------------------"
echo "✅ 合成完成: $TARGET_IMAGE"
echo "提示: 请将其放入手机 DCIM/Camera 目录查看。"
echo "-----------------------------------------------"
