import socket
import os
import ssl
import sys

def fetch(url):
    if "://" not in url:
        raise ValueError("Invalid Url")
    
    schema, rest = url.split("://", 1)

    if "/" in rest:
        host, path = rest.split("/", 1)
        path = "/" + path
    else:
        host = rest
        path = "/"
    
    if schema == "http":
        default_port = 80
    
    elif schema == "https":
        default_port = 443
    
    else:
        raise ValueError("Unsupported Schema")

    """
    What's happening:

    url.split("://", 1) — the 1 means split only on the first occurrence, giving us ["http", "example.com/index.html"]
    We then split rest on the first / to separate the host from the path. If there's no /, the path defaults to "/"
    Port defaults are set based on scheme — 80 for HTTP, 443 for HTTPS. These are universal standards
    """

    host_header = host
    if ":" in host:
        host_only, port_str = host.split(":", 1)

        try:
            port = int(port_str)
            host = host_only
        except ValueError:
            port = default_port
        
    else:
        port = default_port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    from dns_resolver import resolve
    ip = resolve(host)
    if host.lower() == "localhost":
        ip = "127.0.0.1"
    else:
        ip = resolve(host)

    if not ip:    
        raise ValueError("DNS resolver failed")
    
    sock.connect((ip, port)) 
    # sock.connect((host, port))  #dns resolver by os

    if schema == "https":
        context = ssl.create_default_context();
        sock = context.wrap_socket(sock, server_hostname=host)

    """
    What's happening:

    host_header = host — we save the original host string (e.g. localhost:8080) before we strip the port out of it. We need this later for the Host: header in the request
    If the host contains : it means the user specified a custom port like localhost:8080, so we split it and parse the port as an integer
    sock.connect((host, port)) — opens the TCP connection to the server. At this point the "handshake" happens and the connection is live
    HTTPS: for secure connections, we can't just send plain text — everything must be encrypted. ssl.create_default_context() sets up SSL with proper certificate verification, and wrap_socket() upgrades our plain TCP socket into an encrypted one. The server_hostname is needed for SNI (Server Name Indication) — it tells the server which certificate to use, important when one server hosts multiple domains
    """
    
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"HOST: {host_header}\r\n"
        f"User-Agent: simple-browswer\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    sock.sendall(request.encode())

    response = b""

    while True:
        data = sock.recv(4096)
        if not data:
            break
        response += data
    
    sock.close()

    if b"\r\n\r\n" in response:
        header, body = response.split(b"\r\n\r\n", 1)
        
        # check content type to decide how to return
        header_str = header.decode(errors="ignore").lower()
        if "content-type: image" in header_str:
            return body                         # raw bytes for images
        return body.decode(errors="ignore")     # string for html
    else:
        return ""
    
    """
    What's happening:

    The HTTP request is just a formatted string. Each line ends with \r\n (carriage return + newline) — this is required by the HTTP spec, \n alone won't work with all servers
    The headers we're sending:

    Host — required in HTTP/1.1, tells the server which domain we want (important when one IP hosts multiple sites)
    User-Agent — identifies the client, servers sometimes behave differently based on this
    Connection: close — tells the server to close the connection after responding, so our recv loop knows when to stop


    The blank \r\n at the end is critical — it signals the end of the headers
    Why a loop for receiving? Large responses won't fit in one recv() call. recv(4096) reads up to 4096 bytes at a time, so we keep reading until we get empty bytes which means the connection closed
    response.split(b"\r\n\r\n", 1) — splits the response into headers and body on that blank line, same separator we used when sending from the server. We only want the body
    """

from renderer import Browser

def launch(url=None):
    browser = Browser()
    browser.fetch_func = fetch      # inject our fetch function into the renderer

    if url:
        browser.navigate(url)
    
    browser.run()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None
    launch(url)