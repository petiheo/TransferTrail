# Báo cáo Dự án Transfer Trail

## Mục lục
1. [Tổng quan](#1-tổng-quan)
2. [Hướng dẫn chạy phần mềm](#2-hướng-dẫn-chạy-phần-mềm)
3. [Giới thiệu](#3-giới-thiệu)
4. [Kiến trúc Hệ thống](#4-kiến-trúc-hệ-thống)
5. [Giao diện Người dùng](#5-giao-diện-người-dùng)
6. [Thành phần phía Client](#6-thành-phần-phía-client)
7. [Thành phần phía Server](#7-thành-phần-phía-server)
8. [Giao thức giao tiếp (Protocol Communication)](#8-giao-thức-giao-tiếp-protocol-communication)
9. [Xử lý File Lớn](#9-xử-lý-file-lớn)
10. [Bảo mật](#10-bảo-mật)
11. [Mô tả chức năng của các hàm](#11-mô-tả-chức-năng-của-các-hàm)
12. [Kết luận và Hướng phát triển](#12-kết-luận-và-hướng-phát-triển)
13. [Phụ lục](#13-phụ-lục)
14. [Tài liệu tham khảo](#14-tài-liệu-tham-khảo)

## 1. Tổng quan

Transfer Trail là một ứng dụng truyền file client-server được phát triển nhằm tối ưu hóa quá trình truyền file giữa các thiết bị qua mạng. Dự án này nhằm mục đích cung cấp một giải pháp đơn giản, hiệu quả và đáng tin cậy cho việc chia sẻ file mà không cần dựa vào các dịch vụ lưu trữ đám mây của bên thứ ba.

Báo cáo này trình bày chi tiết về kiến trúc, thiết kế và triển khai của Transfer Trail, bao gồm các khía cạnh kỹ thuật, giao diện người dùng, và các tính năng chính của ứng dụng.

## 2. Hướng dẫn chạy phần mềm

### 2.1 Yêu cầu Hệ thống

- Node.js v20.15.1 trở lên ([Link](https://nodejs.org/en)).
- Python 3.12.3 trở lên ([Link](https://www.python.org/downloads/)).
- Electron (sẽ được cài đặt tự động qua npm)

### 2.2 Cài đặt

1. Clone repository hoặc tải source code trên moodle:
   ```
   git clone https://github.com/petiheo/TransferTrail
   cd TransferTrail
   ```

2. Cài đặt dependencies:
   ```
   npm install
   ```

3. Cấu hình:
   - Chỉnh sửa file `config.json` để cấu hình địa chỉ IP và cổng của server.

4. Chạy ứng dụng:
   - Server: `python server/src/app.py`
   - Client: `npm start`

## 3. Giới thiệu

### 3.1 Công nghệ và Thư viện

Transfer Trail được xây dựng dựa trên các công nghệ và thư viện sau:

1. **Electron**: Framework để xây dựng ứng dụng desktop đa nền tảng.
2. **Node.js**: Môi trường runtime JavaScript (v20.15.1 trở lên).
3. **Python**: Ngôn ngữ lập trình cho phía server (Python 3.12.3 trở lên).
4. **Socket Programming**: Kỹ thuật lập trình cho giao tiếp mạng.

#### 3.1.1 Thư viện chuẩn Python

- `socket`: Cho lập trình mạng
- `threading`: Để xử lý đa luồng
- `os`: Cho các thao tác hệ thống
- `struct`: Để đóng gói và giải nén dữ liệu nhị phân
- `time`: Cho các thao tác liên quan đến thời gian
- `uuid`: Để tạo các định danh duy nhất
- `hashlib`: Cho việc tính toán MD5 hash

#### 3.1.2 Module Node.js

- `path`: Để xử lý đường dẫn file
- `os`: Cho các thao tác hệ điều hành
- `util`: Cho các tiện ích
- `child_process`: Để chạy các script Python
- `fs`: Cho các thao tác file system

### 3.2 Tính năng chính

1. Truyền file đa luồng
2. Hỗ trợ file có kích thước lớn
3. Giao diện người dùng thân thiện
4. Khả năng tạm dừng và tiếp tục truyền file
5. Hiển thị tiến trình truyền file theo thời gian thực
6. Tự động phân loại file theo định dạng

## 4. Kiến trúc Hệ thống

### 4.1 Tổng quan Kiến trúc

Transfer Trail sử dụng kiến trúc client-server, kết hợp với mô hình ứng dụng desktop của Electron. Kiến trúc này cho phép ứng dụng hoạt động hiệu quả trên nhiều nền tảng khác nhau, đồng thời tận dụng được sức mạnh của cả JavaScript và Python.

```mermaid
graph TD
    A[Client - Electron App]
    A --> C[UI - HTML/CSS/JS]
    A --> D[Main Process - Node.js]
    A --> E[Renderer Process - Chromium]
    D <-->|IPC| E
    D -->|Invoke| F[Python Scripts]
    F -->|Socket| B[Server - Python]
```

Hình 1: Kiến trúc tổng thể của Transfer Trail

### 4.2 Lý do chọn Electron và Python

1. **Electron**: 
   - Cho phép phát triển ứng dụng desktop đa nền tảng với công nghệ web.
   - Tích hợp sẵn Node.js, mang lại khả năng tương tác mạnh mẽ với hệ thống.
   - Cộng đồng lớn và nhiều tài nguyên hỗ trợ.

2. **Python**: 
   - Hiệu suất cao trong xử lý I/O và mạng.
   - Thư viện chuẩn phong phú cho lập trình mạng và xử lý file.
   - Dễ dàng triển khai logic server phức tạp.

Sự kết hợp này cho phép tận dụng ưu điểm của cả hai công nghệ: giao diện người dùng linh hoạt của Electron và khả năng xử lý mạng mạnh mẽ của Python.

## 5. Giao diện Người dùng

### 5.1 Tổng quan Giao diện

Giao diện người dùng của Transfer Trail được thiết kế với mục tiêu đơn giản, trực quan và dễ sử dụng. Nó bao gồm các thành phần chính sau:

1. Thanh bên (Sidebar)
2. Khu vực tải lên (Upload area)
3. Danh sách file (File list)
4. Thanh tiến trình (Progress bar)
5. Thông báo (Notifications)

### 5.2 Các thành phần UI chính

| Thành phần | Chức năng |
|------------|-----------|
| Thanh bên | Hiển thị các danh mục file và cho phép lọc danh sách file |
| Khu vực tải lên | Cho phép người dùng kéo thả hoặc chọn file để tải lên |
| Danh sách file | Hiển thị các file có sẵn trên server với thông tin chi tiết |
| Thanh tiến trình | Hiển thị tiến độ tải lên/tải xuống file |
| Thông báo | Cung cấp phản hồi về các hoạt động và trạng thái của ứng dụng |

### 5.3 Hình ảnh Giao diện

![Main Interface](./images/main-interface.png)
*Hình 2: Giao diện chính của Transfer Trail*

![Update IP Form](./images/update-ip-form.png)
*Hình 3: Form cập nhật IP Server*

![Download/Upload Progress](./images/progress-display.png)
*Hình 4: Hiển thị tiến độ tải xuống/tải lên*

![Success Notification](./images/success-notification.png)
*Hình 5: Thông báo thành công*

![Error Notification](./images/error-notification.png)
*Hình 6: Thông báo lỗi*

## 6. Thành phần phía Client

### 6.1 Giới thiệu về Electron

Electron là một framework mã nguồn mở cho phép phát triển ứng dụng desktop đa nền tảng sử dụng các công nghệ web. Nó kết hợp Chromium và Node.js vào một runtime duy nhất, cho phép xây dựng ứng dụng bằng HTML, CSS, và JavaScript.

Electron hoạt động dựa trên hai loại tiến trình chính:

1. **Main Process**: Quản lý vòng đời ứng dụng, tạo và quản lý cửa sổ, tương tác với hệ thống.
2. **Renderer Process**: Hiển thị giao diện người dùng và xử lý tương tác người dùng.

```mermaid
graph TD
    A[Electron App] --> B[Main Process]
    A --> C[Renderer Process]
    B <--> C[Renderer Process]
    B <--> D[Native APIs]
    C <--> E[Web Technologies]
    E --> F[HTML]
    E --> G[CSS]
    E --> H[JavaScript]
    
    classDef highlight fill:#f9f,stroke:#333,stroke-width:4px;
    class A,B,C highlight;
```

Hình 7: Cấu trúc cơ bản của ứng dụng Electron

### 6.2 Cấu trúc Thành phần Client

```mermaid
graph TD
    A[Client] --> B[Python Scripts]
    A --> C[Electron Main Process]
    A --> D[Electron Renderer Process]
    A --> E[IPC Communication]
    B --> B1[download_file.py]
    B --> B2[upload_file.py]
    B --> B3[list_files.py]
    C --> C1[app.js]
    C --> C2[ipcHandlers.js]
    D --> D1[main.js]
    D --> D2[fileHandlers.js]
    D --> D3[uiHandlers.js]
    D --> D4[notifications.js]
    E --> E1[preload.js]
```

Hình 8: Cấu trúc thành phần phía Client

#### 6.2.1 Python Scripts

- `download_file.py`: Xử lý tải file từ server.
- `upload_file.py`: Quản lý quá trình tải file lên server.
- `list_files.py`: Lấy danh sách file từ server.

#### 6.2.2 Electron Main Process

- `app.js`: Khởi tạo ứng dụng và quản lý vòng đời.
- `ipcHandlers.js`: Xử lý các sự kiện IPC giữa Main Process và Renderer Process.

#### 6.2.3 Electron Renderer Process

- `main.js`: Khởi tạo giao diện người dùng và xử lý tương tác.
- `fileHandlers.js`: Quản lý các hoạt động liên quan đến file.
- `uiHandlers.js`: Cập nhật giao diện người dùng.
- `notifications.js`: Hiển thị thông báo cho người dùng.

#### 6.2.4 IPC Communication

- `preload.js`: Cầu nối giữa Main Process và Renderer Process, cung cấp các API an toàn cho Renderer Process.

### 6.3 Luồng Dữ liệu

```mermaid
sequenceDiagram
    participant User
    participant Renderer as Renderer Process
    participant Main as Main Process
    participant Python as Python Scripts
    participant Server

    User->>Renderer: Tương tác (ví dụ: nhấn nút tải xuống)
    Renderer->>Main: Gửi yêu cầu qua IPC
    Main->>Python: Thực thi script Python
    Python->>Server: Gửi yêu cầu đến server
    Server->>Python: Trả về dữ liệu
    Python->>Main: Trả về kết quả
    Main->>Renderer: Gửi dữ liệu qua IPC
    Renderer->>User: Cập nhật giao diện người dùng
```

Hình 9: Luồng dữ liệu trong ứng dụng Transfer Trail

## 7. Thành phần phía Server

### 7.1 Cấu trúc Server

```mermaid
graph TD
    A[Server] --> B[app.py]
    A --> C[download_handler.py]
    A --> D[upload_handler.py]
    A --> E[file_list_handler.py]
    A --> F[config.py]
    A --> G[utils.py]
    A --> H[Models]
    H --> I[file_info.py]
    H --> J[message_structure.py]
```

Hình 10: Cấu trúc thành phần phía Server

### 7.2 Chức năng các Module

- `app.py`: Thiết lập server và xử lý kết nối client.
- `download_handler.py`: Xử lý yêu cầu tải xuống file.
- `upload_handler.py`: Xử lý yêu cầu tải lên file.
- `file_list_handler.py`: Quản lý và cung cấp danh sách file.
- `config.py`: Chứa các cấu hình server.
- `utils.py`: Chứa các hàm tiện ích.
- `models/file_info.py`: Định nghĩa cấu trúc thông tin file.
- `models/message_structure.py`: Định nghĩa cấu trúc message giao tiếp.

### 7.3 Xử lý Đồng thời

Server sử dụng mô hình đa luồng để xử lý đồng thời nhiều yêu cầu từ client:

1. Mỗi kết nối client được xử lý trong một luồng riêng biệt.
2. Sử dụng threading pool để quản lý hiệu quả các luồng.
3. Áp dụng lock để đồng bộ hóa truy cập vào tài nguyên chia sẻ.

## 8. Giao thức giao tiếp (Protocol Communication)

### 8.1 Cấu trúc Message

Mỗi message giữa client và server có cấu trúc như sau:

1. 1 byte cho mã hoạt động (op_code)
2. 4 bytes cho độ dài payload
3. Payload (độ dài thay đổi)

```mermaid
graph LR
    A[1 byte op_code] --> B[4 bytes payload length]
    B --> C[Variable-length payload]
```

Hình 11: Cấu trúc message

### 8.2 Các loại Yêu cầu và Phản hồi

| Opcode | Ý nghĩa |
| --- | --- |
| 1 | FILE_LIST_REQUEST |
| 2 | FILE_LIST_RESPONSE |
| 3 | DOWNLOAD_REQUEST |
| 4 | DOWNLOAD_RESPONSE |
| 5 | DOWNLOAD_PART_PORT |
| 6 | DOWNLOAD_PART_NUMBER |
| 7 | DOWNLOAD_INCOMPLETE |
| 8 | UPLOAD_REQUEST |
| 9 | UPLOAD_RESPONSE |
| 10 | UPLOAD_PART_PORT |
| 11 | UPLOAD_PART_NUMBER |
| 12 | UPLOAD_INCOMPLETE |
| 13 | FILE_MD5 |
| 14 | ERROR |

### 8.3 Quy trình giao tiếp

#### File Download Process

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: FILE_LIST_REQUEST
    Server->>Client: FILE_LIST_RESPONSE
    Client->>Server: DOWNLOAD_REQUEST
    Server->>Client: DOWNLOAD_RESPONSE
    loop For each part
        Server->>Client: DOWNLOAD_PART_PORT
        Client->>Server: Connect to port
        Server->>Client: DOWNLOAD_PART_NUMBER
        Server->>Client: File part data
    end
    alt All parts received successfully
        Server->>Client: FILE_MD5
    else Some parts missing
        Server->>Client: DOWNLOAD_INCOMPLETE
        Client->>Server: Request missing parts
        loop For each missing part
            Server->>Client: DOWNLOAD_PART_PORT
            Client->>Server: Connect to port
            Server->>Client: DOWNLOAD_PART_NUMBER
            Server->>Client: File part data
        end
        Server->>Client: FILE_MD5
    end
    Client->>Client: Verify MD5
    Client->>Server: Confirmation

```

Hình 12: Quy trình giao tiếp khi download file

#### File Upload Process

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: UPLOAD_REQUEST
    Server->>Client: UPLOAD_RESPONSE
    loop For each part
        Server->>Client: UPLOAD_PART_PORT
        Client->>Server: Connect to port
        Client->>Server: UPLOAD_PART_NUMBER
        Client->>Server: File part data
    end
    alt All parts received successfully
        Server->>Client: FILE_MD5
    else Some parts missing
        Server->>Client: UPLOAD_INCOMPLETE
        Client->>Server: Send missing parts
        loop For each missing part
            Server->>Client: UPLOAD_PART_PORT
            Client->>Server: Connect to port
            Client->>Server: UPLOAD_PART_NUMBER
            Client->>Server: File part data
        end
        Server->>Client: FILE_MD5
    end
    Client->>Client: Verify MD5
    Client->>Server: Confirmation

```

Hình 13: Quy trình giao tiếp khi upload file

## 9. Xử lý File Lớn

### 9.1 Phân chia File

- File được chia thành nhiều phần nhỏ, mỗi phần có kích thước cố định.
- Số lượng phần được xác định dựa trên kích thước file và cấu hình server.

### 9.2 Truyền Đa luồng

- Mỗi phần file được truyền qua một luồng riêng biệt.
- Sử dụng nhiều kết nối socket đồng thời để tối ưu hóa tốc độ truyền.

### 9.3 Quản lý Bộ nhớ

- Sử dụng kỹ thuật streaming để đọc và ghi file theo từng chunk nhỏ.
- Áp dụng cơ chế buffer để cân bằng giữa hiệu suất và sử dụng bộ nhớ.
- Sau khi nhận một chunk thành công, chương trình sẽ lưu vào ROM để tránh tràn bộ nhớ đệm buffer.

### 9.4 Khôi phục Truyền

- Lưu trữ trạng thái truyền của từng phần file.
- Cho phép tiếp tục truyền từ điểm gián đoạn nếu có lỗi xảy ra.

## 10. Bảo mật

### 10.1 Biện pháp Bảo mật Hiện tại

1. Sử dụng MD5 hash để xác minh tính toàn vẹn của file sau khi truyền.
2. Giới hạn quyền truy cập vào thư mục chứa file trên server.

### 10.2 Kế hoạch Bảo mật Tương lai

1. Triển khai mã hóa end-to-end cho quá trình truyền file.
2. Tích hợp hệ thống xác thực người dùng.
3. Áp dụng HTTPS cho giao tiếp giữa client và server.
4. Triển khai cơ chế kiểm soát truy cập dựa trên vai trò.


## 11. Mô tả chức năng của các hàm

Phần này cung cấp một cái nhìn chi tiết về cách thức hoạt động và tương tác giữa các hàm, lớp, và phương thức trong hệ thống. Việc nghiên cứu phần này sẽ giúp thầy cô có được hiểu biết sâu hơn về cấu trúc và cơ chế vận hành của phần mềm. Tuy nhiên, cần lưu ý rằng những thông tin chi tiết này không phải là bắt buộc để nắm bắt được ý tưởng tổng thể và nguyên lý hoạt động cơ bản của ứng dụng.

### 11.1. Phía Client

#### 11.1.1. Python

##### 11.1.1.1. Các hàm trong config.py

- `load_config()`: Đọc file cấu hình JSON và trả về dữ liệu cấu hình.
- Các biến cấu hình: `HOST`, `SERVER_PORT`, `BUFFER_SIZE`, `FORMAT`, `NUMBER_OF_PARTS`, `RETRY_LIMIT`, `MIN_TIMEOUT`, `MAX_TIMEOUT`, `INITIAL_SPEED`, `CLIENT_DATA_PATH`, `DOWNLOADING_TEMP_PATH`.

##### 11.1.1.2. Các hàm trong download_file.py

- `recv_file_from_server()`: Nhận một phần của file từ server.
- `update_download_progress()`: Cập nhật và in tiến độ tải xuống.
- `handle_thread()`: Xử lý việc tải xuống cho một phần cụ thể của file.
- `assemble_file()`: Lắp ráp các phần file đã tải xuống thành file hoàn chỉnh, cho phép sai số nhỏ trong kích thước cuối cùng.
- `download_file()`: Quản lý quá trình tải xuống toàn bộ file, bao gồm xử lý các phần bị thiếu.

##### 11.1.1.3. Các hàm trong list_files.py

- `recv_list_from_server()`: Nhận danh sách file từ server.
- `main()`: Khởi tạo kết nối và in danh sách file nhận được.

##### 11.1.1.4. Các hàm trong upload_file.py

- `update_upload_progress()`: Cập nhật và in tiến độ tải lên.
- `send_file_to_server()`: Gửi một phần của file lên server.
- `upload_file()`: Quản lý quá trình tải lên toàn bộ file.

##### 11.1.1.5. Các hàm trong utils.py

- `ensure_dir()`: Đảm bảo một thư mục tồn tại, tạo nếu chưa có.
- `calculate_md5()`: Tính toán MD5 hash của một file.

#### 11.1.2. Electron

##### 11.1.2.1. Các hàm trong app.js

- `createWindow()`: Tạo cửa sổ mới của ứng dụng Electron.
- `createMainWindow()`: Tạo cửa sổ chính và thiết lập các xử lý IPC.

##### 11.1.2.2. Các hàm trong ipcHandlers.js

- `getFileList()`: Lấy danh sách file từ server thông qua script Python.
- `uploadFile()`: Xử lý quá trình tải file lên server.
- `downloadFile()`: Xử lý quá trình tải file xuống từ server.
- `updateServerIp()`: Cập nhật địa chỉ IP của server trong file cấu hình.
- `setupIpcHandlers()`: Thiết lập các xử lý IPC cho main process.

##### 11.1.2.3. Các hàm trong preload.js

- Expose các API an toàn cho renderer process thông qua `contextBridge`.

##### 11.1.2.4. Các hàm trong fileHandlers.js

- `handleFileUpload()`: Xử lý việc tải lên một file cụ thể.
- `handleUpload()`: Xử lý sự kiện tải lên file từ giao diện người dùng.
- `setupDragAndDrop()`: Thiết lập chức năng kéo và thả cho việc tải lên file.
- `handleDownload()`: Xử lý sự kiện tải xuống file từ giao diện người dùng.

##### 11.1.2.5. Các hàm trong main.js

- `initializeApp()`: Khởi tạo ứng dụng, thiết lập các sự kiện và cập nhật giao diện.

##### 11.1.2.6. Các hàm trong notifications.js

- `showNotification()`: Hiển thị thông báo cho người dùng.

##### 11.1.2.7. Các hàm trong uiHandlers.js

- `updateFileList()`: Cập nhật danh sách file trên giao diện người dùng.
- `initializeCategoryButtons()`: Khởi tạo các nút danh mục trên thanh bên.

### 11.2. Phía Server

#### 11.2.1. Các hàm trong app.py

- `handle_client()`: Xử lý kết nối từ một client cụ thể.
- `main()`: Khởi động server và lắng nghe các kết nối đến.

#### 11.2.2. Các hàm trong download_handler.py

- `send_file_to_client()`: Gửi một phần của file đến client.
- `download_file()`: Quản lý quá trình gửi toàn bộ file đến client.

#### 11.2.3. Các hàm trong file_list_handler.py

- `send_file_list()`: Gửi danh sách file cho client.

#### 11.2.4. Các hàm trong upload_handler.py

- `recv_file_from_client()`: Nhận một phần của file từ client.
- `handle_thread()`: Xử lý việc nhận file trong một thread riêng biệt.
- `assemble_file()`: Lắp ráp các phần file đã nhận thành file hoàn chỉnh, cho phép sai số nhỏ trong kích thước cuối cùng.
- `upload_file()`: Quản lý quá trình nhận toàn bộ file từ client.

#### 11.2.5. Các hàm trong utils.py

- `ensure_dir()`: Đảm bảo một thư mục tồn tại, tạo nếu chưa có.
- `calculate_md5()`: Tính toán MD5 hash của một file.
- `clean_temp_files()`: Dọn dẹp các file tạm thời sau khi hoàn thành quá trình tải lên.

## 12. Kết luận và Hướng phát triển

Transfer Trail đã đạt được mục tiêu ban đầu là cung cấp một giải pháp truyền file hiệu quả và đáng tin cậy. Dự án đã thành công trong việc:

1. Tạo ra một ứng dụng đa nền tảng với giao diện người dùng thân thiện.
2. Triển khai cơ chế truyền file đa luồng để tối ưu hiệu suất.
3. Xử lý hiệu quả các file có kích thước lớn.

Hướng phát triển trong tương lai:

1. Tích hợp mã hóa end-to-end để tăng cường bảo mật.
2. Phát triển tính năng đồng bộ hóa thư mục.
3. Tích hợp với các dịch vụ lưu trữ đám mây.
4. Cải thiện UI/UX dựa trên phản hồi của người dùng.
5. Tối ưu hóa thuật toán nén để giảm dung lượng truyền tải.

## 13. Phụ lục

### 13.1 Thuật ngữ

- **Electron**: Framework để xây dựng ứng dụng desktop đa nền tảng bằng công nghệ web.
- **IPC (Inter-Process Communication)**: Cơ chế giao tiếp giữa các tiến trình trong Electron.
- **Socket**: Điểm cuối của liên kết giao tiếp hai chiều giữa hai chương trình chạy trên mạng.
- **MD5 Hash**: Thuật toán mã hóa được sử dụng để tạo "dấu vân tay" 128-bit cho một file.

### 13.2 Cấu trúc Thư mục Dự án

```
transfer-trail/
├── client/
│   ├── public/
│   ├── src/
│   │   ├── electron/
│   │   └── renderer/
│   ├── python/
│   ├── config.json
│   └── package.json
├── server/
│   ├── data/
│   ├── src/
│   └── config.json
├── images/
└── README.md
```

## 14. Tài liệu tham khảo

1. Electron Documentation. https://www.electronjs.org/docs/latest/
2. Python Socket Programming. https://docs.python.org/3/library/socket.html
3. Python operating system interfaces. https://docs.python.org/3/library/os.html
4. Node.js Documentation. https://nodejs.org/en/docs/
5. MDN Web Docs. https://developer.mozilla.org/en-US/
6. Python Threading Documentation. https://docs.python.org/3/library/threading.html
7. Các vấn đề, thắc mắc chung. https://stackoverflow.com/, https://www.geeksforgeeks.org/, https://realpython.com/
8. Các tutorial liên quan (electron, python): https://www.youtube.com/