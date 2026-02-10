## Design System – Travel Agent Frontend

### 1. Brand Theme

- **Concept**: Modern digital travel concierge – tối giản, chuyên nghiệp, tạo cảm giác tin cậy khi thao tác với tiền và lịch trình.
- **Tone & Mood**:
  - **Trustworthy**: màu xanh dương đại dương, nhiều khoảng trắng, bố cục rõ ràng.
  - **Calm & Focused**: hạn chế màu quá sặc sỡ, dùng accent có kiểm soát để dẫn hướng hành động.
  - **Effortless**: micro-interaction nhẹ, feedback rõ ràng cho mọi hành động (hover, loading, success/error).

### 2. Color System

> Tất cả mã màu dưới đây sẽ được map vào CSS variables / Tailwind theme (vd: `--primary`, `--accent`, …) để dùng thống nhất trong toàn bộ app.

#### 2.1 Core Palette

- **Primary**
  - `--color-primary-500`: `#0F5FE6` (Deep Oceanic Blue – màu chính cho CTA, link chính)
  - `--color-primary-600`: `#0B4BBC`
  - `--color-primary-700`: `#083894`
  - **Usage**:
    - Nút chính: Đăng nhập, Đăng ký, Search flights, Book now.
    - Link/element thể hiện hành động quan trọng.

- **Secondary**
  - `--color-secondary-500`: `#00A9A5` (Teal – bổ trợ cho primary, mang cảm giác “explore/travel”)
  - `--color-secondary-600`: `#008883`
  - `--color-secondary-100`: `#D9F4F3`
  - **Usage**:
    - Nút phụ, tag trạng thái “info”, background cho sections nổi bật (vd: “Lợi ích khi đặt vé tại Travel Agent”).

- **Accent**
  - `--color-accent-500`: `#FF8A3D` (Sunset Orange – accent dùng có kiểm soát)
  - `--color-accent-600`: `#F56A1D`
  - **Usage**:
    - Các CTA “high intent”: “Pay now”, “Confirm booking”.
    - Badges nhỏ nhấn mạnh (vd: “Best price”, “Limited seat”).

#### 2.2 Neutrals (Gray Scale)

- `--color-neutral-950`: `#020617`
- `--color-neutral-900`: `#0B1120`
- `--color-neutral-800`: `#1E293B`
- `--color-neutral-700`: `#334155`
- `--color-neutral-600`: `#475569`
- `--color-neutral-500`: `#64748B`
- `--color-neutral-400`: `#94A3B8`
- `--color-neutral-300`: `#CBD5F5`
- `--color-neutral-200`: `#E2E8F0`
- `--color-neutral-100`: `#F1F5F9`
- `--color-neutral-50`: `#F8FAFC`

- **Usage**:
  - Text chính: `neutral-900` / `neutral-800`.
  - Text phụ / label: `neutral-600`.
  - Border: `neutral-200` / `neutral-300`.
  - Background app: `neutral-25`–`neutral-50` (dùng Tailwind extended).

#### 2.3 Semantic Colors

- **Success**
  - `--color-success-500`: `#16A34A`
  - `--color-success-50`: `#ECFDF3`
  - **Usage**: trạng thái thanh toán thành công, booking confirmed, toast “Saved”.

- **Error**
  - `--color-error-500`: `#DC2626`
  - `--color-error-50`: `#FEF2F2`
  - **Usage**: lỗi validate form, lỗi API, banner cảnh báo.

- **Warning**
  - `--color-warning-500`: `#F59E0B`
  - `--color-warning-50`: `#FFFBEB`
  - **Usage**: cảnh báo về thời gian giữ chỗ, vé sắp hết, session sắp hết hạn.

- **Info**
  - `--color-info-500`: `#0EA5E9`
  - `--color-info-50`: `#E0F2FE`
  - **Usage**: thông báo trung tính, tips, helper text.

### 3. Typography

- **Base font family**:
  - Primary: `Inter`, system fallback: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.
  - Lý do: Inter đọc tốt trên UI hiện đại, hỗ trợ text tiếng Việt tốt, quen thuộc với app SaaS.

#### 3.1 Type Scale

> Dùng rem để dễ scale theo root. Line-height ưu tiên 1.3–1.6 tùy cấp độ để giữ UI thoáng.

- **Display / Hero**
  - `display-1`: 3rem (48px), `line-height: 1.1`, weight 700 – dùng rất tiết kiệm (hero chính).
  - `display-2`: 2.25rem (36px), `line-height: 1.15`, weight 600 – sub-hero / section title lớn.

- **Headings**
  - `h1`: 2rem (32px), `line-height: 1.2`, weight 600.
  - `h2`: 1.5rem (24px), `line-height: 1.3`, weight 600.
  - `h3`: 1.25rem (20px), `line-height: 1.35`, weight 600.
  - `h4`: 1.125rem (18px), `line-height: 1.4`, weight 500.

- **Body**
  - `body-1`: 1rem (16px), `line-height: 1.5`, weight 400 – text chính.
  - `body-2`: 0.875rem (14px), `line-height: 1.5`, weight 400 – mô tả phụ, helper text.

- **UI / Meta**
  - `label`: 0.75rem (12px), `line-height: 1.4`, weight 500, letter-spacing nhẹ – cho label input, pill, badge.
  - `mono` (optional): `0.875rem`, font `SF Mono, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace` – dùng hạn chế cho code / technical text nếu cần.

### 4. Spacing System

> Toàn bộ layout và components sẽ sử dụng scale này để đảm bảo rhythm nhất quán (Tailwind sẽ được cấu hình tương ứng).

- **Base unit**: 4px.
- **Scale**:
  - `space-1`: 4px
  - `space-2`: 8px
  - `space-3`: 12px
  - `space-4`: 16px
  - `space-5`: 20px
  - `space-6`: 24px
  - `space-8`: 32px
  - `space-10`: 40px
  - `space-12`: 48px

- **Usage guidelines**:
  - Khoảng cách giữa label và input: `space-2` (8px).
  - Khoảng cách giữa các field trong form: `space-4` (16px).
  - Padding card: `space-5` (20px) desktop, `space-4` mobile.
  - Section vertical padding: `space-8`–`space-12` tùy độ quan trọng.

### 5. Radius, Elevation & Borders

#### 5.1 Border-radius

- `radius-xs`: 4px – cho chip, badge nhỏ.
- `radius-sm`: 6px – input, button nhỏ.
- `radius-md`: 10px – card, modal, surface chính.
- `radius-lg`: 16px – hero containers, prominent panels.
- `radius-full`: 999px – pill buttons, avatar.

**Guideline**:
- Không dùng bo tròn quá “trẻ con” (vd 24px mọi nơi); ưu tiên cảm giác soft nhưng vẫn chuyên nghiệp.
- Nút và input trong cùng một form dùng chung radius (thường `radius-sm` hoặc `radius-md`).

#### 5.2 Shadows & Elevation

- `shadow-soft-sm`: `0 1px 2px rgba(15, 23, 42, 0.06)`
- `shadow-soft-md`: `0 10px 30px rgba(15, 23, 42, 0.10)`
- `shadow-soft-lg`: `0 24px 60px rgba(15, 23, 42, 0.18)`

**Usage**:
- Card thông tin (booking, flight offer): `shadow-soft-sm` + border `neutral-200`.
- Modal / bottom sheet: `shadow-soft-md`.
- Popover / dropdown: `shadow-soft-sm`, blur background nhẹ nếu cần.

### 6. Layout & Breakpoints

- **Max content width**: 1120–1200px cho desktop.
- **Breakpoints chính** (align với Tailwind):
  - `sm`: 640px – mobile lớn.
  - `md`: 768px – tablet.
  - `lg`: 1024px – laptop.
  - `xl`: 1280px – desktop.
  - `2xl`: 1536px – large desktop.

**Responsive principles**:
- Mobile-first; các màn Auth, Search, Booking phải dùng pattern 1 cột rõ ràng, nút full-width, sticky bottom CTA khi cần (vd “Search flights”).
- Trên desktop, sử dụng grid 2–3 cột cho nội dung: left (form/filter) – right (results/summary).

### 7. Component Patterns (shadcn/ui + Tailwind)

> shadcn/ui sẽ được customize theo palette & radius ở trên. Dưới đây là định hướng cho các nhóm component chính.

- **Buttons**
  - Variants:
    - `primary`: nền `primary-500`, text trắng, hover `primary-600`, focus ring `primary-200`.
    - `secondary`: nền trắng / `neutral-50`, border `neutral-200`, text `neutral-800`, hover `neutral-100`.
    - `ghost`: không border, background transparent, hover `neutral-100`.
    - `destructive`: nền `error-500`, hover `error-600`.
  - Size:
    - `md`: height 40px, px 16px, radius `radius-sm`.
    - `lg`: height 44px, px 20px – cho CTA chính.

- **Inputs / Select / DatePicker**
  - Height 40px, radius `radius-sm`, border `neutral-200`, focus border `primary-500` + ring nhạt.
  - Error state: border `error-500`, helper text `error-500`, background `error-50` rất nhẹ (không quá chói).

- **Cards**
  - Background: trắng (`#FFFFFF`), radius `radius-md`, border `neutral-200`, shadow `shadow-soft-sm`.
  - Dùng consistent padding (`space-5`), header area có optional icon (Lucide).

- **Navigation**
  - Top Nav: background trắng, border-bottom `neutral-200`, height ~64px.
  - Desktop: logo trái, links trung tâm/phải, avatar + menu user phải.
  - Mobile: logo + icon menu; sử dụng sheet/overlay của shadcn cho menu.

### 8. Motion & Micro-interactions

- **Library**: `framer-motion`.

Guidelines:
- Transition tiêu chuẩn:
  - Duration: 150–220ms cho hover/focus.
  - Easing: `easeOut` / `cubic-bezier(0.16, 1, 0.3, 1)` (spring-like, tự nhiên).
- **Hover states**:
  - Buttons: subtle scale `1.01` + shadow nhẹ, không bounce quá đà.
  - Cards: translateY(-1–2px) + shadow tăng rất nhẹ, cursor pointer khi có thể click.
- **Page / Section transitions**:
  - Dùng fade + slide nhẹ (5–10px) khi chuyển giữa các màn lớn (Auth → Dashboard → Booking flow).
- **Feedback**:
  - Dùng `AnimatePresence` cho toasts, modals, skeletons khi mount/unmount.

### 9. Loading, Skeletons & Empty States

- **Skeletons**:
  - Sử dụng skeleton placeholders thay vì spinner cho:
    - Flight search results.
    - Booking list / detail.
    - Profile & passengers.
  - Hình khối skeleton bám theo layout thực tế (vd: khối card travel, avatar circle + lines cho text).

- **Spinners**:
  - Chỉ dùng spinner inline, nhỏ trong nút (vd: “Searching…” trong button) hoặc các action rất ngắn.

- **Empty states**:
  - Bookings trống: illustration nhẹ + message “Bạn chưa có đặt chỗ nào” + CTA “Tìm chuyến bay”.
  - Search results trống: text rõ ràng, gợi ý thay đổi ngày/chặng, có link nhanh “Thử lại với gợi ý phổ biến”.

### 10. Forms & Validation UX

- Sử dụng **React Hook Form + Zod** với:
  - Validation message ngắn gọn, rõ ràng, ưu tiên tiếng Việt (vd: “Email không hợp lệ”, “Mật khẩu tối thiểu 8 ký tự”).
  - Error hiển thị ngay dưới field, không show alert lớn trừ lỗi global (API fail).
- Với Auth (Login/Register):
  - Focus auto vào field đầu tiên.
  - Nút submit disabled + loading state trong khi gọi API.
  - Nếu lỗi 401/409: hiển thị inline message trên form, không popup modal.

### 11. Theming & Dark Mode (Optional Phase)

- Phase đầu: ưu tiên **light theme** chuẩn.
- Thiết kế token ngay từ đầu để có thể thêm dark mode sau:
  - Màu nền, text, border đều lấy từ CSS variables (`--background`, `--foreground`, `--muted`, …).
  - Components shadcn sẽ override dựa trên token, không hard-code hex trực tiếp trong JSX.

---

Design system này sẽ được map sang:

- Cấu hình Tailwind (`tailwind.config.ts`).
- Theme của shadcn/ui (`components.json` & layer `@layer base`).
- Utilities `cn()` cho việc compose classnames sạch sẽ, tránh trùng lặp.

Trong các bước tiếp theo, frontend sẽ implement theo tiêu chuẩn này ngay từ layout, Auth pages, Dashboard, đến flow Search/Booking.
