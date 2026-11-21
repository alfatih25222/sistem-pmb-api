from datetime import datetime
from enum import Enum as PyEnum
import re
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError

# --- 1. KONFIGURASI DATABASE ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./pmb.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. MODEL DATABASE (SQLALCHEMY) ---
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
    kode = Column(String(3), unique=True, nullable=False)
    nama = Column(String(100), nullable=False)
    fakultas = Column(String(100), nullable=False)

    calon_mahasiswa = relationship("CalonMahasiswa", back_populates="prodi")

class CalonMahasiswa(Base):
    __tablename__ = "calon_mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    nama_lengkap = Column(String(150), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    tanggal_lahir = Column(DateTime, nullable=False)
    alamat = Column(Text, nullable=False)
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    jalur_masuk = Column(Enum(JalurEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    nim = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)

    prodi = relationship("ProgramStudi", back_populates="calon_mahasiswa")

# --- 3. VALIDASI PYDANTIC ---
class CalonMahasiswaCreate(BaseModel):
    nama_lengkap: str
    email: str
    phone: str
    tanggal_lahir: datetime
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

# --- 4. INISIALISASI & SEEDING DATABASE ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistem PMB API", version="1.0.0")

def init_db():
    db_session = SessionLocal()
    try:
        prodi_check = db_session.query(ProgramStudi).first()
        if not prodi_check:
            default_prodi = ProgramStudi(id=1, kode="001", nama="Teknik Informatika", fakultas="Teknik")
            db_session.add(default_prodi)
            db_session.commit()
    finally:
        db_session.close()

init_db()

# --- 5. NIM GENERATOR ---
def generate_nim(tahun: int, kode_prodi: str, db: Session) -> str:
    prefix = f"{tahun}{kode_prodi}"
    
    last_student = (
        db.query(CalonMahasiswa)
        .filter(CalonMahasiswa.nim.like(f"{prefix}%"))
        .order_by(CalonMahasiswa.id.desc())
        .with_for_update()
        .first()
    )
    
    if last_student and last_student.nim:
        try:
            last_running_num = int(last_student.nim.split("-")[-1])
            running_num = last_running_num + 1
        except ValueError:
            running_num = 1
    else:
        running_num = 1
        
    return f"{prefix}-{running_num:04d}"

# --- 6. API ENDPOINTS ---
@app.post("/api/pmb/register", status_code=status.HTTP_201_CREATED)
def register_calon_mahasiswa(data: CalonMahasiswaCreate, db: Session = Depends(get_db)):
    prodi = db.query(ProgramStudi).filter(ProgramStudi.id == data.program_studi_id).first()
    if not prodi:
        raise HTTPException(status_code=400, detail="Program studi tidak ditemukan")
    
    existing = db.query(CalonMahasiswa).filter(CalonMahasiswa.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar sebagai calon mahasiswa")
    
    new_candidate = CalonMahasiswa(
        nama_lengkap=data.nama_lengkap,
        email=data.email,
        phone=data.phone,
        tanggal_lahir=data.tanggal_lahir,
        alamat=data.alamat,
        program_studi_id=data.program_studi_id,
        jalur_masuk=data.jalur_masuk,
        status=StatusEnum.PENDING
    )
    
    try:
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Terjadi konflik data")
        
    return {"message": "Pendaftaran berhasil", "id": new_candidate.id, "status": new_candidate.status}

@app.get("/api/pmb/status/{id}")
def get_status_pendaftaran(id: int, db: Session = Depends(get_db)):
    candidate = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Data pendaftar tidak ditemukan")
        
    return {
        "id": candidate.id,
        "nama_lengkap": candidate.nama_lengkap,
        "email": candidate.email,
        "status": candidate.status,
        "nim": candidate.nim,
        "approved_at": candidate.approved_at
    }

@app.put("/api/pmb/approve/{id}")
def approve_candidate(id: int, db: Session = Depends(get_db)):
    candidate = db.query(CalonMahasiswa).filter(CalonMahasiswa.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Data pendaftar tidak ditemukan")
        
    if candidate.status == StatusEnum.APPROVED and candidate.nim:
        return {
            "message": "Pendaftar sudah disetujui sebelumnya",
            "nim": candidate.nim,
            "status": candidate.status
        }
        
    prodi = db.query(ProgramStudi).filter(ProgramStudi.id == candidate.program_studi_id).first()
    current_year = datetime.now().year
    generated_nim = generate_nim(current_year, prodi.kode, db)
    
    candidate.status = StatusEnum.APPROVED
    candidate.nim = generated_nim
    candidate.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(candidate)
    
    return {
        "message": "Pendaftaran berhasil disetujui",
        "nim": candidate.nim,
        "status": candidate.status
    }

@app.get("/api/pmb/stats")
def get_stats(db: Session = Depends(get_db)):
    total_pendaftar = db.query(CalonMahasiswa).count()
    pending = db.query(CalonMahasiswa).filter(CalonMahasiswa.status == StatusEnum.PENDING).count()
    approved = db.query(CalonMahasiswa).filter(CalonMahasiswa.status == StatusEnum.APPROVED).count()
    rejected = db.query(CalonMahasiswa).filter(CalonMahasiswa.status == StatusEnum.REJECTED).count()
    
    return {
        "total_pendaftar": total_pendaftar,
        "pending": pending,
        "approved": approved,
        "rejected": rejected
    }