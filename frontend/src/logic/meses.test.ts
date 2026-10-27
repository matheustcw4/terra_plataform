import { describe, expect, test } from "vitest";
import { ehMes, mesCurto, mesDaData, somarMeses } from "./meses";

describe("meses", () => {
  test("somarMeses atravessa a virada do ano nos dois sentidos", () => {
    expect(somarMeses("2025-11", 3)).toBe("2026-02");
    expect(somarMeses("2026-06", -11)).toBe("2025-07");
    expect(somarMeses("2026-01", -1)).toBe("2025-12");
  });

  test("mesCurto aceita a data da API e o mês do filtro", () => {
    expect(mesCurto("2025-07-01")).toBe("jul/25");
    expect(mesCurto("2026-12")).toBe("dez/26");
    expect(mesDaData("2025-07-01")).toBe("2025-07");
  });

  test("ehMes recusa texto incompleto e mês 13", () => {
    expect(ehMes("2025-07")).toBe(true);
    expect(ehMes("2025-7")).toBe(false);
    expect(ehMes("2025-13")).toBe(false);
    expect(ehMes("")).toBe(false);
  });
});
