# Free-HLS

这是一个免费的 HLS 视频解决方案，即所谓的视频床。本项目提供一整套集成化解决方案，囊括了各环节所需的切片、转码、上传、即时分享等套件。让你可以以更方便、更低廉的方式分享你的视频到任意地方。

本项目仅供学习交流使用，在使用过程中对你或他人造成的任何损失我们概不负责。

## 服务端

服务端位于项目的 `web` 目录，负责向客户端提供视频发布所必要的 API 接口。以及最终目标视频的播放服务。

### 1. 安装依赖

安装最新的 Python3，以及必要包：

```bash
apt install -y python3 python3-pip
pip3 install Flask peewee gunicorn python-dotenv
```

### 2. 启动服务

```bash
cd web
gunicorn app:app -b 0.0.0.0:3395 --workers=5 --threads=2 -D
```

## 客户端

客户端，即 `up.py` 入口，提供对上传视频资源的切片、转码、上传的支持。可以在你的任意机器上使用，只要你安装了必要的依赖项和作出了正确的配置。

### 1. 安装依赖

安装最新的 Python3，以及必要包：

```bash
apt install -y ffmpeg python3 python3-pip
pip3 install requests python-dotenv
```

### 2. 配置服务

正确施行 [服务端](#服务端) 一节的全部内容，完成服务端的搭建。复制客户端配置文件 `.env.example` 为 `.env`，修改其中的 `APIURL` 配置项为你的服务器域名或 IP 地址。

将你的上传驱动器复制到 `uploader` 目录，并在 `.env` 中完成相应的配置。若没有驱动器，请参考 [自定义驱动器](https://github.com/sxyazi/free-hls/wiki/%E8%87%AA%E5%AE%9A%E4%B9%89%E9%A9%B1%E5%8A%A8%E5%99%A8) 该文章。

### 3. 开始使用

准备好目标视频文件，输入如下指令开始切片、上传：

```bash
python3 up.py test.mp4            #默认标题
python3 up.py test.mp4 测试标题    #自定义标题
python3 up.py test.mp4 测试标题 5  #自定义分段大小

python3 ls.py    #列出已上传视频
python3 ls.py 3  #列出已上传视频（第3页，50每页）
```

## 相似服务

- [https://github.com/sxzz/free-hls.js](https://github.com/sxzz/free-hls.js)
- [https://github.com/sxzz/free-hls-live](https://github.com/sxzz/free-hls-live)
- [https://github.com/MoeClub/Note/tree/master/ffmpeg](https://github.com/MoeClub/Note/tree/master/ffmpeg)
