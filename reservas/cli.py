import sys
import argparse
import json
from pathlib import Path
from reservas.repositorio import (
    crear_reserva,
    cancelar_reserva,
    listar_reservas,
    consultar_disponibilidad,
    reiniciar_base,
    ErrorSuperposicion,
    ErrorCancelacion
)
from reservas.validacion import ErrorValidacion

def main(argv=None):
    parser = argparse.ArgumentParser(description="Sistema de reservas de equipos de laboratorio")
    parser.add_argument("--db", default="data/reservas.db", help="Ruta a la base de datos SQLite")
    parser.add_argument("--ahora", default=None, help="Simula la fecha actual en formato 'AAAA-MM-DD HH:MM'")

    subparsers = parser.add_subparsers(dest="comando", required=True)

    # unidades
    subparsers.add_parser("unidades", help="Lista el inventario")

    # disponibilidad
    parser_disp = subparsers.add_parser("disponibilidad", help="Consulta disponibilidad de una unidad")
    parser_disp.add_argument("unidad")
    parser_disp.add_argument("inicio")
    parser_disp.add_argument("fin")

    # reservar
    parser_res = subparsers.add_parser("reservar", help="Crea una reserva")
    parser_res.add_argument("unidad")
    parser_res.add_argument("solicitante")
    parser_res.add_argument("inicio")
    parser_res.add_argument("fin")

    # cancelar
    parser_canc = subparsers.add_parser("cancelar", help="Cancela una reserva por ID")
    parser_canc.add_argument("id", type=int)

    # listar
    parser_list = subparsers.add_parser("listar", help="Lista las reservas")
    parser_list.add_argument("--unidad", default=None)

    # reiniciar
    parser_rein = subparsers.add_parser("reiniciar", help="Reinicia la base de datos")
    parser_rein.add_argument("--confirmar", action="store_true", help="Confirma el borrado de todas las reservas")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0

    try:
        if args.comando == "unidades":
            inv_path = Path("data/inventario.json")
            if inv_path.exists():
                with open(inv_path, "r", encoding="utf-8") as f:
                    inventario = json.load(f)
                for item in inventario:
                    print(f"{item['id']} - {item['equipo']}")
            return 0

        elif args.comando == "disponibilidad":
            disponible = consultar_disponibilidad(
                args.unidad, args.inicio, args.fin,
                ahora=args.ahora, ruta_db=args.db
            )
            if disponible:
                print("disponible")
            else:
                print("no disponible")
            return 0

        elif args.comando == "reservar":
            reserva = crear_reserva(
                args.unidad, args.solicitante, args.inicio, args.fin,
                ahora=args.ahora, ruta_db=args.db
            )
            print(f"Reserva creada con ID {reserva['id']}: {reserva['unidad']} - {reserva['solicitante']} ({reserva['inicio']} a {reserva['fin']}, {reserva['estado']})")
            return 0

        elif args.comando == "cancelar":
            cancelar_reserva(args.id, ruta_db=args.db)
            print(f"Reserva {args.id} cancelada con éxito.")
            return 0

        elif args.comando == "listar":
            reservas = listar_reservas(unidad=args.unidad, ruta_db=args.db)
            if not reservas:
                print("No hay reservas registradas.")
            else:
                for r in reservas:
                    print(f"ID: {r['id']} | Unidad: {r['unidad']} | Solicitante: {r['solicitante']} | Inicio: {r['inicio']} | Fin: {r['fin']} | Estado: {r['estado']}")
            return 0

        elif args.comando == "reiniciar":
            if not args.confirmar:
                print("Error: El comando reiniciar borra todas las reservas de la base de datos. Debe utilizar la opción --confirmar.", file=sys.stderr)
                return 1
            reiniciar_base(ruta_db=args.db)
            print("Base de datos reiniciada con éxito.")
            return 0

    except (ErrorValidacion, ErrorSuperposicion, ErrorCancelacion) as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0
