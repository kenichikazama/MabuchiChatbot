# Hướng dẫn Deploy lên Streamlit Cloud

## Bước 1: Chuẩn bị Repository GitHub

1. Tạo repository mới trên GitHub (có thể private)
2. Push các file sau lên GitHub:
   - `app_cloud.py` (đổi tên thành `streamlit_app.py` hoặc giữ nguyên)
   - `requirements_cloud.txt` (đổi tên thành `requirements.txt`)

```bash
git init
git add app_cloud.py requirements_cloud.txt
git commit -m "Initial commit for Streamlit Cloud"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Bước 2: Đăng nhập Streamlit Cloud

1. Truy cập: https://share.streamlit.io/
2. Đăng nhập bằng GitHub account
3. Click "New app"

## Bước 3: Deploy App

1. Chọn repository bạn vừa tạo
2. Branch: `main`
3. Main file path: `app_cloud.py` (hoặc `streamlit_app.py` nếu bạn đổi tên)
4. Click "Deploy!"

## Bước 4: Cấu hình Secrets

**QUAN TRỌNG**: Bạn cần thêm secrets vào Streamlit Cloud

1. Sau khi deploy, click vào ⚙️ Settings
2. Chọn "Secrets"
3. Thêm nội dung sau:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
MICROSOFT_ACCOUNT = "your_email@mabuchi-motor.com"
MICROSOFT_PASSWORD = "your_password"
AI_MODEL = "gemini-2.0-flash"
SHAREPOINT_SITE_URL = "https://mabmotor-my.sharepoint.com/personal/vnm13649_mabuchi-motor_com"
SHAREPOINT_FILE_URL = "/personal/vnm13649_mabuchi-motor_com/Documents/Microsoft Teams Chat Files/guest_information 1.xlsx"
```

4. Click "Save"
5. App sẽ tự động restart

## Bước 5: Xác nhận

- URL của app sẽ có dạng: `https://your-app-name.streamlit.app`
- Share URL này cho đồng nghiệp sử dụng!

## Lưu ý quan trọng

1. **Free tier limitations:**
   - 1GB RAM
   - App sẽ sleep sau 7 ngày không dùng
   - Có thể có cold start delay

2. **Secrets bảo mật:**
   - KHÔNG commit .env hoặc secrets vào GitHub
   - Luôn dùng Streamlit Secrets cho thông tin nhạy cảm

3. **Nếu app crash:**
   - Check logs tại Settings > Logs
   - Đảm bảo requirements.txt đúng

## Troubleshooting

### Lỗi "ModuleNotFoundError"
- Kiểm tra requirements.txt có đầy đủ packages

### Lỗi "KeyError" với secrets
- Đảm bảo đã thêm tất cả secrets cần thiết

### Lỗi SharePoint connection
- Kiểm tra lại MICROSOFT_ACCOUNT và MICROSOFT_PASSWORD
- Đảm bảo account có quyền truy cập file

---
Made with ❤️ for Year-End Party Chatbot
