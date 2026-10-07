-- ============================================================
--  schema.sql — ร้านค้าออนไลน์ (Mini Online Shop) — ธีมอุปกรณ์คอมพิวเตอร์ (PC Parts)
--  ชื่อตาราง/คอลัมน์ต้องตรงกับที่ db.py เรียกใช้ (cust_id, product_id, order_id)
-- ============================================================
 
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS order_line;
DROP TABLE IF EXISTS shop_order;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS customer;
 
-- ---------- ลูกค้า ----------
CREATE TABLE customer (
    cust_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE,
    address     VARCHAR(255),
    tier        VARCHAR(20) NOT NULL DEFAULT 'regular'   -- regular / silver / gold
);
 
-- ---------- สินค้า ----------
CREATE TABLE product (
    product_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50),
    price       DECIMAL(10,2) NOT NULL,
    stock       INT NOT NULL DEFAULT 0
);
 
-- ---------- ออเดอร์ ----------
CREATE TABLE shop_order (
    order_id    INT AUTO_INCREMENT PRIMARY KEY,
    cust_id     INT NOT NULL,
    order_date  DATE NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',   -- pending/paid/shipped/completed/cancelled
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
);
 
-- ---------- รายการสินค้าในออเดอร์ (M:N #1: shop_order x product) ----------
CREATE TABLE order_line (
    order_id    INT NOT NULL,
    product_id  INT NOT NULL,
    qty         INT NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,   -- เก็บราคา ณ ตอนสั่ง (ไม่อิง product.price ที่เปลี่ยนได้)
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES shop_order(order_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
 
-- ---------- รีวิวสินค้า (M:N #2: customer x product) ----------
CREATE TABLE review (
    cust_id     INT NOT NULL,
    product_id  INT NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     VARCHAR(255),
    review_date DATE NOT NULL,
    PRIMARY KEY (cust_id, product_id),
    FOREIGN KEY (cust_id) REFERENCES customer(cust_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
 
-- ---------- การชำระเงิน (weak entity ของ shop_order, 1:1) ----------
CREATE TABLE payment (
    payment_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT NOT NULL UNIQUE,
    method      VARCHAR(20) NOT NULL,     -- cash / credit_card / transfer / promptpay
    amount      DECIMAL(10,2) NOT NULL,
    paid_date   DATE,
    FOREIGN KEY (order_id) REFERENCES shop_order(order_id)
);
 
-- ============================================================
--  SAMPLE DATA
-- ============================================================
 
INSERT INTO customer (name, email, address, tier) VALUES
('สมชาย ใจดี',      'somchai@mail.com', 'กรุงเทพฯ',   'gold'),
('สมหญิง รักเรียน',  'somying@mail.com', 'เชียงใหม่',  'silver'),
('วิชัย มั่งมี',      'wichai@mail.com',  'ขอนแก่น',    'regular'),
('มานี มีนา',        'manee@mail.com',   'ภูเก็ต',     'gold'),
('ประยุทธ ตั้งใจ',   'prayut@mail.com',  'กาฬสินธุ์',  'regular'),
('อรทัย สุขใจ',      'orathai@mail.com', 'อุดรธานี',   'silver'),
('ธนพล รุ่งเรือง',   'thanapon@mail.com','นครราชสีมา', 'regular'),
('ปิยะดา แสงทอง',    'piyada@mail.com',  'สุราษฎร์ธานี','regular');
 
-- สินค้า: อุปกรณ์คอมพิวเตอร์ (PC Parts) — ใช้ชื่อรุ่นจริงเพื่อความสมจริงตอนพรีเซนต์
INSERT INTO product (name, category, price, stock) VALUES
('NVIDIA GeForce RTX 4070',        'การ์ดจอ',      23900.00, 10),
('AMD Ryzen 7 7800X3D',            'ซีพียู',       12900.00, 15),
('Corsair Vengeance DDR5 32GB',    'แรม',           4290.00, 40),
('ASUS ROG STRIX B650-A',          'เมนบอร์ด',      7990.00, 20),
('Corsair RM750x',                 'พาวเวอร์ซัพพลาย', 4590.00, 25),
('NZXT H510',                      'เคสคอมพิวเตอร์', 2990.00, 30),
('Samsung 980 Pro 1TB NVMe',       'SSD',           3490.00, 45),
('Logitech G502 HERO',             'เมาส์เกมมิ่ง',   1890.00, 100),
('Razer BlackWidow V4',            'คีย์บอร์ดเกมมิ่ง', 4990.00, 50),
('HyperX Cloud II',                'หูฟังเกมมิ่ง',   2290.00, 60);
 
INSERT INTO shop_order (cust_id, order_date, status) VALUES
(1, '2026-08-01', 'completed'),
(1, '2026-08-15', 'completed'),
(2, '2026-08-03', 'completed'),
(3, '2026-08-05', 'completed'),
(4, '2026-08-06', 'completed'),
(4, '2026-08-20', 'shipped'),
(5, '2026-08-07', 'completed'),
(6, '2026-08-09', 'completed'),
(7, '2026-08-10', 'pending'),
(8, '2026-08-12', 'completed'),
(3, '2026-08-25', 'cancelled');   -- order_id=11: ยกเลิก ไม่มี payment (ไว้ทดสอบว่ารายงานไม่นับ)
 
-- order_line: ให้ "เมาส์ Logitech G502" (product_id=8) ขายดีที่สุด (ของถูก ซื้อบ่อย)
-- ส่วนการ์ดจอ/ซีพียู (product_id=1,2) ราคาสูงแต่ขายน้อยชิ้น เพื่อดันยอดซื้อของบางลูกค้าให้สูงกว่าค่าเฉลี่ยชัดเจน
INSERT INTO order_line (order_id, product_id, qty, unit_price) VALUES
(1, 1, 1, 23900.00),
(1, 8, 2, 1890.00),
(2, 10, 1, 2290.00),
(2, 7, 1, 3490.00),
(3, 2, 1, 12900.00),
(3, 4, 1, 7990.00),
(4, 8, 4, 1890.00),
(4, 6, 1, 2990.00),
(5, 10, 2, 2290.00),
(5, 5, 1, 4590.00),
(6, 3, 1, 4290.00),
(6, 8, 1, 1890.00),
(7, 8, 5, 1890.00),
(7, 7, 2, 3490.00),
(8, 10, 1, 2290.00),
(8, 9, 1, 4990.00),
(9, 7, 2, 3490.00),
(10, 8, 3, 1890.00),
(10, 6, 1, 2990.00),
(11, 1, 3, 23900.00);   -- ออเดอร์ที่ถูกยกเลิก (ต้องไม่ถูกนับในรายงาน)
 
-- review: เมาส์ (8) และหูฟัง (10) คะแนนเฉลี่ยสูง >=4 ชัดเจน
-- การ์ดจอ (1) คะแนนต่ำเป็นตัวเทียบ (ของแพงแต่ร้อน/เสียงดัง), SSD (7) พอดี = 4.0 (เคสขอบ)
INSERT INTO review (cust_id, product_id, rating, comment, review_date) VALUES
(1, 8, 5, 'ลื่นมาก จับถนัดมือ', '2026-08-05'),
(2, 8, 4, 'คุ้มราคา ปุ่มไม่แข็ง', '2026-08-06'),
(3, 8, 5, 'ใช้เล่นเกมดีมาก', '2026-08-07'),
(1, 10, 5, 'เสียงดี ใส่สบายทั้งวัน', '2026-08-08'),
(4, 10, 4, 'คุณภาพเสียงโอเค', '2026-08-09'),
(5, 10, 5, 'ชอบมาก คุ้มราคา', '2026-08-10'),
(2, 1, 3, 'แรงดีแต่ร้อนไปหน่อย', '2026-08-11'),
(6, 1, 2, 'พัดลมดังกว่าที่คิด', '2026-08-12'),
(7, 7, 4, 'อ่านเขียนไวมาก', '2026-08-13');
 
-- payment: จ่ายเฉพาะออเดอร์ที่ completed/shipped (order_id=9 เป็น pending ยังไม่จ่าย)
INSERT INTO payment (order_id, method, amount, paid_date) VALUES
(1,  'credit_card', 27680.00, '2026-08-01'),
(2,  'promptpay',    5780.00, '2026-08-15'),
(3,  'transfer',    20890.00, '2026-08-03'),
(4,  'cash',        10550.00, '2026-08-05'),
(5,  'credit_card',  9170.00, '2026-08-06'),
(6,  'transfer',     6180.00, '2026-08-20'),
(7,  'promptpay',   16430.00, '2026-08-07'),
(8,  'cash',         7280.00, '2026-08-09'),
(10, 'promptpay',    8660.00, '2026-08-12');

-- ตรวจผล
SHOW TABLES;
SELECT COUNT(*) FROM customer;
SELECT COUNT(*) FROM order_line;
