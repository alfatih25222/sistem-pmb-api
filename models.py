from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class JalurEnum(str, PyEnum):
    SNBP = "SNBP"
    SNBT = "SNBT"
    MANDIRI = "Mandiri"

class StatusEnum(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ProgramStudi(Base):
    __tablename__ = "program_studi"

    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(3), unique=True, nullable=False)  # Contoh: 001
    nama = Column(String(100), nullable=False)
    fakultas = Column(String(100), nullable=False)

    calon_mahasiswa = relationship("CalonMahasiswa", back_populates="prodi")

class CalonMahasiswa(Base):
    __tablename__ = "calon_mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    nama_lengkap = Column(String(150), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)  # Validasi format Indonesia di level Pydantic/API
    tanggal_lahir = Column(DateTime, nullable=False)
    alamat = Column(Text, nullable=False)
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    jalur_masuk = Column(Enum(JalurEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    nim = Column(String(20), unique=True, nullable=True)  # Diisi saat approve
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)

    prodi = relationship("ProgramStudi", back_populates="calon_mahasiswa")