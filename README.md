# Nitgen Service Windows

1. **Buat Virtual Environment**

```
python3 -m venv .venv
```

2. **Install Package**

Setelah virtual environment dibuat, install package yang diperlukan dengan perintah berikut:

```
/path/to/.venv/bin/pip install -r requirements.txt
```

3. **Buka Task Scheduler**

Tekan tombol Windows dan ketik "Task Scheduler" untuk membuka aplikasi Task Scheduler. Setelah aplikasi terbuka, klik **Create Task** yang ada di panel sebelah kanan.

4. **Konfigurasi Task Scheduler**

Di dalam jendela **Create Task**, atur pengaturan seperti berikut:

**Tab General:**

- Nama Task `Fingerprint Monitoring Service Nitgen`.
- Diskripsi `Monitoring perubahan file NITGENDBAC.mdb`.
- Pilih **Run whether user is logged on or not dan ceklist Do not store password**.
- Ceklist **Run with highest privileges**.

**Tab Triggers:**

- Klik **New...** untuk menambahkan trigger.
- Pilih **At Startup** untuk running auto startup windows

**Tab Actions:**

- Klik **New...** untuk menambahkan action.
- Pilih **Start a program**.
- Di kolom **Program/script**, masukkan path ke Python executable (misalnya: `C:\Python39\python.exe`).
- Di kolom **Add arguments (optional)**, masukkan path lengkap ke skrip Python (misalnya `C:\path\to\your\script.py`).
- Di kolom **Start in (optional)**, masukkan path ke skrip Python (misalnya `C:\path\to\your`).

**Tab Settings:**

- Pilih **Allow task to be run on demand** jika Anda ingin menjalankan task secara manual.
- Pilih **If the task fails, restart every** dan tentukan berapa kali task akan dicoba ulang jika gagal.

5. **Simpan dan Jalankan Task**

Setelah semua pengaturan selesai, klik **OK** untuk menyimpan task.
