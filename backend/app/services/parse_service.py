import difflib
from dataclasses import dataclass

from app.core.utils import parse_loads, slugify, short_hash


@dataclass
class PlanExercise:
    sessao_nome: str
    exercicio_id: str
    exercicio_nome_canonico: str
    sets: int
    reps_alvo: int
    aliases: list[str]


@dataclass
class ParsedPlan:
    exercises: list[PlanExercise]


@dataclass
class ParsedCarga:
    exercicio_nome: str
    loads: list[float]


@dataclass
class ParsedCargasMessage:
    items: list[ParsedCarga]


def parse_plan_message(message: str) -> ParsedPlan:
    lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
    if not lines or lines[0].upper() != "PLANO":
        raise ValueError("Mensagem precisa começar com PLANO")

    exercises: list[PlanExercise] = []
    current_session = None
    for line in lines[1:]:
        if "|" not in line:
            current_session = line.strip().upper()
            continue
        if not current_session:
            raise ValueError("Sessão não definida")
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            raise ValueError("Linha de exercício inválida")
        nome = parts[0]
        sets = int(parts[1])
        reps = int(parts[2])
        aliases = []
        if len(parts) > 3 and parts[3]:
            aliases = [alias.strip().lower() for alias in parts[3].split(",") if alias]
        slug = slugify(nome)
        exercicio_id = f"{slug}-{short_hash(nome)}"
        exercises.append(
            PlanExercise(
                sessao_nome=current_session,
                exercicio_id=exercicio_id,
                exercicio_nome_canonico=nome,
                sets=sets,
                reps_alvo=reps,
                aliases=aliases,
            )
        )
    return ParsedPlan(exercises=exercises)


def parse_cargas_message(message: str) -> ParsedCargasMessage:
    lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
    if not lines:
        raise ValueError("Mensagem vazia")
    if lines[0].upper().startswith("CARGAS"):
        lines = lines[1:]
    items: list[ParsedCarga] = []
    for line in lines:
        if ":" not in line:
            continue
        name, load_str = line.split(":", 1)
        loads = parse_loads(load_str)
        if not loads:
            continue
        items.append(ParsedCarga(exercicio_nome=name.strip(), loads=loads))
    if not items:
        raise ValueError("Nenhuma carga válida encontrada")
    return ParsedCargasMessage(items=items)


def match_exercise(
    exercicio_nome: str,
    plan_exercises: list[PlanExercise],
    threshold: float = 0.88,
) -> PlanExercise | None:
    target = exercicio_nome.strip().lower()
    exact_map = {ex.exercicio_nome_canonico.lower(): ex for ex in plan_exercises}
    if target in exact_map:
        return exact_map[target]
    alias_map = {}
    for ex in plan_exercises:
        for alias in ex.aliases:
            alias_map[alias.lower()] = ex
    if target in alias_map:
        return alias_map[target]
    best_score = 0.0
    best_exercise = None
    for ex in plan_exercises:
        score = difflib.SequenceMatcher(
            None, target, ex.exercicio_nome_canonico.lower()
        ).ratio()
        if score > best_score:
            best_score = score
            best_exercise = ex
    if best_score >= threshold:
        return best_exercise
    return None
