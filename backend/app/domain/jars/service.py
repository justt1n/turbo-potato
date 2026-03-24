from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.jars.model import CreateInput, Jar, UpdateInput


class JarRepository(Protocol):
    def create_jar(self, jar: Jar) -> Jar: ...

    def update_jar(self, current_code: str, jar: Jar) -> Jar: ...

    def list_jars(self) -> list[Jar]: ...


@dataclass(slots=True)
class DefaultJarSeedResult:
    created: int
    skipped: int
    items: list[dict[str, str]]


class JarService:
    def __init__(self, repo: JarRepository) -> None:
        self._repo = repo

    def create(self, input_data: CreateInput) -> Jar:
        code = normalize_code(input_data.code)
        name = input_data.name.strip()
        kind = input_data.kind.strip() or "cash"
        if not code:
            raise ValueError("code is required")
        if not name:
            raise ValueError("name is required")
        if input_data.opening_balance < 0:
            raise ValueError("openingBalance must be zero or greater")
        actual_balance = input_data.actual_balance if input_data.actual_balance is not None else input_data.opening_balance
        if actual_balance < 0:
            raise ValueError("actualBalance must be zero or greater")
        if any(existing.code == code for existing in self._repo.list_jars()):
            raise ValueError(f"jar {code} already exists")

        jar = Jar(
            code=code,
            name=name,
            kind=kind,
            openingBalance=input_data.opening_balance,
            actualBalance=actual_balance,
            isActive=input_data.is_active,
            note=input_data.note.strip(),
        )
        return self._repo.create_jar(jar)

    def update(self, current_code: str, input_data: UpdateInput) -> Jar:
        code = normalize_code(current_code)
        name = input_data.name.strip()
        kind = input_data.kind.strip() or "cash"
        if not code:
            raise ValueError("code is required")
        if not name:
            raise ValueError("name is required")
        if input_data.opening_balance < 0:
            raise ValueError("openingBalance must be zero or greater")
        if input_data.actual_balance < 0:
            raise ValueError("actualBalance must be zero or greater")

        jar = Jar(
            code=code,
            name=name,
            kind=kind,
            openingBalance=input_data.opening_balance,
            actualBalance=input_data.actual_balance,
            isActive=input_data.is_active,
            note=input_data.note.strip(),
        )
        return self._repo.update_jar(code, jar)

    def list(self) -> list[Jar]:
        return self._repo.list_jars()

    def seed_default_jars(self) -> DefaultJarSeedResult:
        existing_codes = {item.code for item in self._repo.list_jars()}
        created = 0
        skipped = 0
        items: list[dict[str, str]] = []

        for definition in default_jar_definitions():
            if definition.code in existing_codes:
                skipped += 1
                items.append({"code": definition.code, "name": definition.name, "status": "skipped"})
                continue

            self.create(definition)
            created += 1
            items.append({"code": definition.code, "name": definition.name, "status": "created"})
            existing_codes.add(definition.code)

        return DefaultJarSeedResult(created=created, skipped=skipped, items=items)


def normalize_code(value: str) -> str:
    return value.strip().replace(" ", "_")


def default_jar_definitions() -> list[CreateInput]:
    return [
        CreateInput(code="ThietYeu", name="Chi tiêu thiết yếu", kind="bucket", note="Ăn uống, đi lại, điện nước, vận hành cơ bản."),
        CreateInput(code="TuDoTaiChinh", name="Tự do tài chính", kind="bucket", note="Phần tích lũy dài hạn để mở rộng vùng an toàn tài chính."),
        CreateInput(code="GiaoDuc", name="Giáo dục", kind="bucket", note="Học tập, sách, khóa học, nâng cấp năng lực."),
        CreateInput(code="HuongThu", name="Hưởng thụ", kind="bucket", note="Cafe, giải trí, du lịch ngắn ngày, vui chơi có chủ đích."),
        CreateInput(code="TietKiemMucTieu", name="Tiết kiệm mục tiêu", kind="bucket", note="Quỹ dành cho các mục tiêu chi tiêu lớn đã có kế hoạch."),
        CreateInput(code="ChoDi", name="Cho đi", kind="bucket", note="Biếu tặng, hỗ trợ gia đình, đóng góp cộng đồng."),
    ]
