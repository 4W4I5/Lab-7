from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.responses import RedirectResponse


# Data class to hold data on students
class Student(SQLModel, table=True):
    SerialNo: int | None = Field(default=None, primary_key=True)
    FName: str = Field(index=True)
    LName: str
    Email: str = Field(index=True)


# DB Setup
sqlite_file_name = "./awais_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/add_student")
async def add_student(
    session: SessionDep,
    fname: str = Form(...),
    lname: str = Form(...),
    email: str = Form(...),
):
    new_student = Student(FName=fname, LName=lname, Email=email)
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    print(f"Added Student: {new_student}")
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete_student/{serial_no}")
async def delete_student(serial_no: int, session: SessionDep):
    student_to_delete = session.get(Student, serial_no)
    if not student_to_delete:
        raise HTTPException(status_code=404, detail="Student not found")

    session.delete(student_to_delete)
    session.commit()
    print(f"Deleted Student with SerialNo: {serial_no}")
    return RedirectResponse(url="/", status_code=303)


@app.post("/update/{serial_no}")
async def update_student(
    serial_no: int,
    session: SessionDep,
    fname: str = Form(...),
    lname: str = Form(...),
    email: str = Form(...),
):
    student_to_update = session.get(Student, serial_no)
    if not student_to_update:
        raise HTTPException(status_code=404, detail="Student not found")

    # Update student details
    student_to_update.FName = fname
    student_to_update.LName = lname
    student_to_update.Email = email
    session.commit()
    print(f"Updated Student with SerialNo: {serial_no}")

    return RedirectResponse(url="/", status_code=303)


@app.get("/update/{serial_no}")
async def edit_student(serial_no: int, request: Request, session: SessionDep):
    student_to_edit = session.get(Student, serial_no)
    if not student_to_edit:
        raise HTTPException(status_code=404, detail="Student not found")

    templates = Jinja2Templates(directory="./templates")
    return templates.TemplateResponse(
        "update.html", {"request": request, "student": student_to_edit}
    )


@app.get("/")
async def root(request: Request, session: SessionDep):
    statement = select(Student).offset(0).limit(100)
    allStudents = session.exec(statement).all()
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse(
        "index.html", {"request": request, "students": allStudents}
    )


@app.get("/Awais")
async def retMyName():
    return {"message": "Welcome to Awais's Home Page"}
