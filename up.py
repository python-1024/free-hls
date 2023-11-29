import argparse
import os
import re
import json
from os import path
from os import getenv as _
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import (api, exec, execstr, tsfiles, uploader,
                    manageurl, sameparams, genslice, genrepair)

def encrypt(code):
    # 如果未启用加密，直接返回原始代码
    if not _('ENCRYPTION') == 'YES':
        return code

    # 遍历所有 ts 文件，进行加密
    for file in tsfiles(code):
        if file.startswith('enc.'):
            continue

        print(f'正在对 {file} 进行加密，生成 enc.{file} ... ', end='')
        key = exec(['openssl','rand','16']).hex()
        iv  = execstr(['openssl','rand','-hex','16'])
        exec(['openssl','aes-128-cbc','-e','-in',file,'-out','enc.%s' % file,'-p','-nosalt','-iv',iv,'-K',key])

        # 将密钥信息发送到 API
        key_id = api('POST', 'key', data={'iv': iv, 'key': key})
        if not key_id:
            open('out.m3u8', 'w').write(code)
            print('失败')
            exit(1)

        print('完成')
        # 在原始 M3U8 播放列表中添加加密信息
        code = re.sub(f'(#EXTINF:.+$[\\r\\n]+^{file}$)', '#EXT-X-KEY:METHOD=AES-128,URI="%s/play/%s.key",IV=0x%s\n\\1' % (_('APIURL'), key_id, iv), code, 1, re.M)
        code = code.replace(file, f'enc.{file}')

    # 将加密后的代码写入文件
    open('out.m3u8', 'w').write(code)
    return code

def publish(code, title=None):
    # 如果设置为不使用服务器，输出信息并返回
    if _('NOSERVER') == 'YES':
        return print('m3u8 文件已保存至 tmp/out.m3u8')

    # 发布视频到服务器
    r = api('POST', 'publish', data={'code': code, 'title': title,
                                     'params': json.dumps(uploader().params())})
    if r:
        url = '%s/play/%s' % (_('APIURL'), r['slug'])
        print(f'该视频已发布至: {url}')
        print(f'你也可以直接下载: {url}.m3u8')
        print('---')
        print('点击此处编辑该视频信息:\n%s' % manageurl(f'video/{r["id"]}'))

def repairer(code):
    # 设置单个文件的大小上限
    limit = uploader().MAX_BYTES

    # 检查每个 ts 文件的大小，如果超过上限，尝试进行修复
    for file in tsfiles(code):
        if path.getsize(file) > limit:
            tmp = 'rep.%s' % file
            os.system(genrepair(file, tmp, limit * 8))
            os.rename(tmp, file)

            # 如果修复后仍然超过上限，输出信息并退出
            if path.getsize(file) > limit:
                open('out.m3u8', 'w').write(code)
                print(f'文件过大: tmp/{file}')
                print('请调整参数或继续使用相同参数执行')
                exit(2)

    # 将修复后的代码写入文件
    open('out.m3u8', 'w').write(code)
    return code


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='视频文件')
    parser.add_argument('title', type=str, nargs='?', help='发布标题')
    parser.add_argument('time', type=int, nargs='?', help='预分段时间', default=0)
    parser.add_argument('-c, --config', type=str, dest='config', help='更改配置文件路径')
    args = parser.parse_args()

    # 从配置文件中加载环境变量
    load_dotenv(args.config)
    tmpdir  = path.dirname(path.abspath(__file__)) + '/tmp'
    command = genslice(path.abspath(args.file), args.time)

    # 切换到临时目录
    if sameparams(tmpdir, command):
        os.chdir(tmpdir)
    else:
        os.mkdir(tmpdir)
        os.chdir(tmpdir)
        os.system(command)
        open('command.sh', 'w').write(command)

    failures, completions = 0, 0
    # 加密并修复视频
    lines = encrypt(repairer(open('out.m3u8', 'r').read()))

    # 使用线程池并发地上传视频片段
    executor = ThreadPoolExecutor(max_workers=15)
    futures  = {executor.submit(uploader().handle, chunk): chunk for chunk in tsfiles(lines)}

    for future in as_completed(futures):
        completions += 1
        result = future.result()

        if not result:
            failures += 1
            print('[%s/%s] 上传失败: %s' % (completions, len(futures), futures[future]))
            continue

        lines = lines.replace(futures[future], result)
        print('[%s/%s] 已上传 %s 至 %s' % (completions, len(futures), futures[future], result))

    # 将结果写入文件
    open('out.m3u8', 'w').write(lines)
    open('params.json', 'w').write(json.dumps(uploader().params()))

    if failures:
        print('部分成功: %d/%d' % (completions-failures, completions))
        print('你可以使用相同参数重新执行此程序')
        exit(2)

    publish(lines, args.title or path.splitext(path.basename(args.file))[0])


if __name__ == '__main__':
    main()
