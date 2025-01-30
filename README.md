# Nitgen Service Windows

- Dokumentasi ini menjelaskan cara menginstal dan menjalankan aplikasi Nitgen Service Webhook sebagai service di Windows menggunakan Python dan NSSM (Non-Sucking Service Manager).

## 1. Install Python

- Install python dulu versi 3.10.6:  
  [https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe](https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe)
- Setelah instalasi selesai, buka command prompt dan jalankan perintah berikut untuk memverifikasi versi python yang terinstal:

```
python --version
```

- Jika versi python yang terinstal sudah sesuai dengan versi yang dibutuhkan, maka akan muncul output seperti ini:

```
Python 3.10.6
```

- Jika tidak menampilkan versi Python yang diinstall, maka PATH belum ditambahkan dengan benar. Untuk menambahkan PATH di Windows, ikuti langkah-langkah berikut.

## 2. Menambahkan Python ke PATH

1. **Buka System Properties:**

   - Tekan `Windows + X` pada keyboard dan pilih **System**.

   - Pada jendela System, klik **Advanced system settings** di sisi kiri.

2. **Masuk ke Environment Variables:**

   - Di jendela System Properties, klik tombol **Environment Variables** yang ada di bagian bawah.

3. **Cari Path di Environment Variables:**

   - Pada bagian **System variables**, cari dan pilih variabel yang bernama `Path`, lalu klik **Edit**.

4. **Tambahkan Path Python:**

   - Di jendela Edit Environment Variables, klik **New** dan tambahkan dua path berikut (pastikan untuk mengganti `C:\Python10` dengan direktori tempat Python terinstal jika berbeda):

   - `C:\Python10\` (atau direktori Python yang sesuai)

5. **Simpan Perubahan:**

   - Klik **OK** di semua jendela yang terbuka untuk menyimpan perubahan.
   - Setelah itu Verifikasi versi python yang terinstal seperti cara sebelumnya.

## 3. Install NSSM

- NSSM digunakan untuk menjalankan aplikasi Python sebagai service di Windows. Ikuti langkah-langkah berikut untuk menginstal NSSM:

1. Download NSSM dari situs resminya:  
   [https://nssm.cc/](https://nssm.cc/)

2. Pilih versi yang sesuai dengan sistem operasi kamu (32-bit atau 64-bit).

3. Ekstrak file ZIP yang diunduh ke folder yang diinginkan, misalnya `C:\nssm`.

4. Tambahkan folder `nssm` ke dalam Path environment variable untuk mempermudah penggunaan.

## 4. Install Project Nitgen Service

1. Buat Virtual Environment di dalam folder `nitgen-service`

```
python -m venv .venv
```

2. **Install Package**

Setelah virtual environment dibuat, install package yang diperlukan dengan perintah berikut:

```
/path/to/.venv/bin/pip install -r requirements.txt
```

## 5. Install Nitgen Service menggunakan NSSM

1.  **Buka Command Prompt (CMD) sebagai Administrator**

- Tekan tombol Windows dan ketik `cmd`, lalu pilih "Run as Administrator" untuk membuka Command Prompt dengan hak akses Administrator.

2.  **Install Service dengan NSSM**

- Di Command Prompt, navigasikan ke folder tempat Anda mengekstrak NSSM (misalnya: `cd C:\path\to\nssm`).
- Jalankan perintah berikut untuk menginstall service:
  ```bash
  nssm install NitgenServiceWebhook
  ```
- Setelah menjalankan perintah di atas, jendela konfigurasi NSSM akan muncul.

3.  **Konfigurasi NSSM**

- **Path**: Klik "Browse" dan pilih executable Python Anda, misalnya `C:\Python9\python.exe`.
- **Arguments**: Di kolom ini, masukkan path lengkap ke skrip Python Anda (misalnya: `C:\path\to\your\main.py`).
- **Startup directory**: Di sini, masukkan direktori di mana skrip Python Anda berada (misalnya: `C:\path\to\your`).

4.  **Pengaturan Lainnya di NSSM**

- Klik pada tab **I/O** dan pastikan untuk mengarahkan log ke file tertentu jika Anda ingin menangkap output dan error dari service.
- Klik **Install Service** setelah semua pengaturan selesai.

5.  **Konfigurasi Agar Service Start Otomatis**

- Setelah service terinstall, buka **Services** di Windows dengan mengetik `services.msc` di Start menu.
- Temukan service yang baru saja Anda buat dengan nama **NitgenServiceWebhook**.
- Klik kanan pada service tersebut, pilih **Properties**, dan atur **Startup type** menjadi **Automatic** agar service berjalan otomatis saat startup.

6.  **Start Service**

- Klik kanan pada service tersebut dan pilih **Start** untuk menjalankan service.

7.  **Verifikasi Service Berjalan**

- Untuk memastikan service berjalan dengan baik, Anda dapat memeriksa di **Task Manager** atau menggunakan perintah berikut di Command Prompt:
  ```bash
  sc qc NitgenServiceWebhook
  ```
- Jika service berjalan dengan benar, Anda akan melihat informasi terkait status dan konfigurasi service.
