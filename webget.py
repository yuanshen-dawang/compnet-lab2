import socket
import sys

USAGE = "usage: python webget.py host path [port]"


def main():
    # 参数不足：只给 0 个或 1 个参数时打印用法并退出
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(1)

    host = sys.argv[1]
    path = sys.argv[2]

    # 端口可选，缺省 80
    port = 80
    if len(sys.argv) > 3:
        try:
            port = int(sys.argv[3])
        except ValueError:
            print("port must be an integer")
            print(USAGE)
            sys.exit(1)

    # 容错：路径没写斜杠时自动补上
    if not path.startswith("/"):
        path = "/" + path

    # 用路径最后一段作为输出文件名，根路径则存为 index.html
    name = path.rstrip("/").split("/")[-1]
    if not name:
        name = "index.html"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))

    req = (
        "GET " + path + " HTTP/1.1\r\n"
        "Host: " + host + "\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    s.sendall(req.encode())

    # 循环接收，两种结束条件
    buf = b""
    header_end = -1
    content_length = None
    calls = 0
    sizes = []

    while True:
        data = s.recv(4096)
        if not data:
            break
        calls += 1
        sizes.append(len(data))
        buf += data
        if header_end < 0:
            i = buf.find(b"\r\n\r\n")
            if i >= 0:
                header_end = i + 4
                for line in buf[:i].decode("iso-8859-1").split("\r\n")[1:]:
                    low = line.lower()
                    if low.startswith("content-length:"):
                        content_length = int(line.split(":", 1)[1].strip())
        if content_length and len(buf) - header_end >= content_length:
            break
    s.close()

    # 拆响应
    sep = buf.find(b"\r\n\r\n")
    if sep < 0:
        print("response header not found")
        sys.exit(1)

    head = buf[:sep].decode("iso-8859-1")
    body = buf[sep + 4:]

    lines = head.split("\r\n")
    print("status line:", lines[0])
    parts = lines[0].split(" ", 2)
    if len(parts) >= 2:
        print("status code:", parts[1])
    print("-" * 40)
    for h in lines[1:]:
        print("  " + h)
    print("-" * 40)
    print("recv calls:", calls)
    print("sizes:", sizes)
    print("head bytes:", sep + 4)
    print("body bytes:", len(body))

    # 二进制写入，保证图片不被破坏
    with open(name, "wb") as f:
        f.write(body)
    print("saved to:", name)


if __name__ == "__main__":
    main()
