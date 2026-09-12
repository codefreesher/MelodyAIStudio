# Desktop verification key

Copy public PEM do Admin tạo vào `license_public.pem` trong thư mục này.
Không đặt private key tại đây. Khi chưa có public key, ứng dụng vẫn mở được,
nhưng kích hoạt báo lỗi cấu hình. Public key là trust anchor của bản phân phối;
không nhận public key từ nội dung license hoặc người dùng nhập license.
