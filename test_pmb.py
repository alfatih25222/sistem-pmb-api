import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app, get_db
from models import ProgramStudi, JalurEnum

# Setup database testing in-memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Tambahkan dummy program studi untuk keperluan test
    prodi = ProgramStudi(id=1, kode="001", nama="Teknik Informatika", fakultas="Teknik")
    db.add(prodi)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_register_success():
    response = client.post("/api/pmb/register", json={
        "nama_lengkap": "Budi Santoso",
        "email": "budi@example.com",
        "phone": "081234567890",
        "tanggal_lahir": "2005-05-12",
        "alamat": "Jl. Merdeka No. 10",
        "program_studi_id": 1,
        "jalur_masuk": "SNBP"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data

def test_register_duplicate_email():
    payload = {
        "nama_lengkap": "Ani Wati",
        "email": "ani@example.com",
        "phone": "081298765432",
        "tanggal_lahir": "2005-08-20",
        "alamat": "Jl. Sudirman No. 5",
        "program_studi_id": 1,
        "jalur_masuk": "SNBT"
    }
    # Registrasi pertama sukses
    client.post("/api/pmb/register", json=payload)
    # Registrasi kedua dengan email sama harus error 409 conflict
    response = client.post("/api/pmb/register", json=payload)
    assert response.status_code == 409

def test_approve_generate_nim_and_idempotent():
    # 1. Register
    res = client.post("/api/pmb/register", json={
        "nama_lengkap": "Joko Susilo",
        "email": "joko@example.com",
        "phone": "081122334455",
        "tanggal_lahir": "2005-01-01",
        "alamat": "Jl. Ahmad Yani",
        "program_studi_id": 1,
        "jalur_masuk": "Mandiri"
    })
    candidate_id = res.json()["id"]

    # 2. Approve pertama (Generate NIM)
    approve_res1 = client.put(f"/api/pmb/approve/{candidate_id}")
    assert approve_res1.status_code == 200
    nim_1 = approve_res1.json()["nim"]
    assert nim_1 is not None

    # 3. Approve kedua (Idempotent test: tidak generate ulang NIM baru)
    approve_res2 = client.put(f"/api/pmb/approve/{candidate_id}")
    assert approve_res2.status_code == 200
    nim_2 = approve_res2.json()["nim"]
    assert nim_1 == nim_2

def test_invalid_phone_format():
    response = client.post("/api/pmb/register", json={
        "nama_lengkap": "Siti Badriah",
        "email": "siti@example.com",
        "phone": "12345",  # Invalid format telepon Indonesia
        "tanggal_lahir": "2005-03-10",
        "alamat": "Jl. Kebon Jeruk",
        "program_studi_id": 1,
        "jalur_masuk": "SNBP"
    })
    assert response.status_code == 422 # Error validasi Pydantic