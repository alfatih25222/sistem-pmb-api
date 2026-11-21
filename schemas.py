import re
from datetime import date
from pydantic import BaseModel, EmailStr, field_validator
from models import JalurEnum  # Perbaikan di sini (menghilangkan titik .)

class CalonMahasiswaCreate(BaseModel):
    nama_lengkap: str
    email: EmailStr
    phone: str
    tanggal_lahir: date
    alamat: str
    program_studi_id: int
    jalur_masuk: JalurEnum

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = r'^(\+62|62|0)8[1-9][0-9]{6,10}$'
        if not re.match(pattern, v):
            raise ValueError('Format nomor telepon Indonesia tidak valid')
        return v