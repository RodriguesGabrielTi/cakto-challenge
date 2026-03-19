from decimal import Decimal

from injector import singleton

from src.common.constants import CENTS_MULTIPLIER, PERCENT_BASE


@singleton
class SplitCalculator:
    """
    Distribui o valor líquido entre recebedores usando o Método do Maior Resto.

    Trabalha em centavos (inteiros) para evitar imprecisão de ponto flutuante.
    A diferença entre o total e a soma das partes truncadas é distribuída
    1 centavo por vez, priorizando quem teve a maior perda fracionária.
    """

    def calculate(self, net_amount: Decimal, splits: list[dict]) -> list[dict]:
        total_cents = int(net_amount * CENTS_MULTIPLIER)

        allocations = self._compute_base_allocations(total_cents, splits)
        self._distribute_leftover(total_cents, allocations)

        return self._to_result(allocations)

    def _compute_base_allocations(self, total_cents: int, splits: list[dict]) -> list[dict]:
        """Calcula a parte base (floor) de cada recebedor e guarda o resto fracionário."""
        return [self._allocate_one(total_cents, split) for split in splits]

    @staticmethod
    def _allocate_one(total_cents: int, split: dict) -> dict:
        percent = Decimal(str(split["percent"]))
        exact = total_cents * percent / PERCENT_BASE
        floored = int(exact)

        return {
            "recipient_id": split["recipient_id"],
            "role": split["role"],
            "floored": floored,
            "remainder": exact - floored,
        }

    @staticmethod
    def _distribute_leftover(total_cents: int, allocations: list[dict]) -> None:
        """Distribui os centavos restantes para quem teve maior perda fracionária."""
        distributed = sum(a["floored"] for a in allocations)
        leftover = total_cents - distributed

        allocations.sort(key=lambda a: a["remainder"], reverse=True)

        for i in range(leftover):
            allocations[i]["floored"] += 1

    @staticmethod
    def _to_result(allocations: list[dict]) -> list[dict]:
        return [
            {
                "recipient_id": allocation["recipient_id"],
                "role": allocation["role"],
                "amount": Decimal(allocation["floored"]) / Decimal(str(CENTS_MULTIPLIER)),
            }
            for allocation in allocations
        ]
