# Multi-Browser Card Checker - CHEWY.COM

## Tính năng

✅ **Chạy 5 browser cùng lúc** để check card song song, giảm thời gian  
✅ **Mỗi account tối đa 4 thẻ LIVE** - sau đó tự động tạo account mới  
✅ **Tự động clear form** khi thẻ DIE để check thẻ tiếp theo  
✅ **Multiprocessing** - mỗi browser chạy trong process riêng  

## Cách sử dụng

### 1. Chuẩn bị file cards

Tạo file `cards.txt` với format:
```
number|month|year|cvv
```

Ví dụ:
```
4532015112830366|12|2025|123
5425233430109903|11|2026|456
4916338506082832|09|2027|789
```

### 2. Chạy Multi-Browser Checker

```bash
python3 multi_checker_chewy.py
```

### 3. Hoặc chạy Single Browser

```bash
python3 card_checker_chewy.py
```

## Cấu hình

Trong file `multi_checker_chewy.py`:

```python
checker = MultiBrowserChecker(
    num_browsers=5,           # Số browser chạy cùng lúc
    max_live_per_account=4    # Số thẻ LIVE tối đa mỗi account
)
```

## Flow hoạt động

### Initialization (1 lần mỗi account):
1. Mở homepage
2. Đăng ký account mới
3. Click vào sản phẩm
4. Add product vào cart
5. View cart
6. Click Checkout
7. Điền shipping address
8. **Kết thúc ở payment form**

### Check Card (mỗi thẻ):
1. Điền Name on Card (random tên Mỹ)
2. Điền Card Number
3. Chọn Exp Month (dropdown)
4. Chọn Exp Year (dropdown)
5. Điền CVV
6. Click "Use Card"
7. Đợi response
8. Check kết quả:
   - **LIVE** → Thẻ được add vào account
   - **DIE** → Clear form và check thẻ tiếp

### Khi đủ 4 thẻ LIVE:
1. Đóng browser hiện tại
2. Mở browser mới
3. Tạo account mới
4. Tiếp tục check các thẻ còn lại

## Kết quả

Sau khi chạy xong, sẽ hiển thị tổng kết:

```
======================================================================
KẾT QUẢ TỔNG HỢP
======================================================================
[Worker 1] [✓] 4532015112830366|12|2025|123: APPROVED - Thẻ hợp lệ
[Worker 2] [✗] 5425233430109903|11|2026|456: DECLINED - Thẻ bị từ chối
...
======================================================================
LIVE: 15 | DIE: 35 | ERROR: 0 | TOTAL: 50
======================================================================
```

## Lưu ý

- Mỗi browser sẽ chạy độc lập trong process riêng
- Delay 1 giây giữa các browser khi khởi động để tránh quá tải
- Khi thẻ DIE, chỉ clear: Name on Card, Card Number, Exp Month, Exp Year, CVV
- KHÔNG xóa: Billing Address, Shipping Address, Giỏ hàng

## Troubleshooting

### Lỗi "No module named 'seleniumbase'"
```bash
pip install seleniumbase
```

### Browser bị crash
- Giảm `num_browsers` xuống 3 hoặc 2
- Tăng delay giữa các browser

### Quá nhiều account bị block
- Thêm delay giữa các thẻ
- Sử dụng proxy
