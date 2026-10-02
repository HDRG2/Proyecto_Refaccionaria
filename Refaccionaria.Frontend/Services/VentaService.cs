using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Services;

public class VentaService
{
    private readonly IRepository<Venta> _repoVentas;
    private readonly IRepository<DetalleVenta> _repoDetalleVentas;
    private readonly IRepository<Refaccion> _repoRefacciones;


    public VentaService(
        IRepository<Venta> repoVentas,
        IRepository<DetalleVenta> repoDetalleVentas,
        IRepository<Refaccion> repoRefacciones)
    {
        _repoVentas = repoVentas
            ?? throw new ArgumentNullException(nameof(repoVentas));

        _repoDetalleVentas = repoDetalleVentas
            ?? throw new ArgumentNullException(nameof(repoDetalleVentas));

        _repoRefacciones = repoRefacciones
            ?? throw new ArgumentNullException(nameof(repoRefacciones));
    }


    // =========================================================
    // REGISTRAR VENTA
    // =========================================================

    public async Task<Venta> RegistrarVentaAsync(
        Usuario usuario,
        IEnumerable<DetalleVenta> lineasTicket,
        string metodoPago,
        decimal recibido)
    {
        // -----------------------------------------------------
        // 1. VALIDAR DATOS BÁSICOS
        // -----------------------------------------------------

        if (usuario == null)
        {
            throw new InvalidOperationException(
                "No existe un usuario válido para realizar la venta."
            );
        }

        if (!usuario.Activo)
        {
            throw new InvalidOperationException(
                "El usuario no está activo."
            );
        }

        List<DetalleVenta> lineas =
            lineasTicket?.ToList()
            ?? throw new InvalidOperationException(
                "No se recibió información del ticket."
            );

        if (lineas.Count == 0)
        {
            throw new InvalidOperationException(
                "No se puede registrar una venta sin productos."
            );
        }

        if (string.IsNullOrWhiteSpace(metodoPago))
        {
            throw new InvalidOperationException(
                "Debes seleccionar un método de pago."
            );
        }


        // -----------------------------------------------------
        // 2. OBTENER INVENTARIO REAL
        // -----------------------------------------------------

        await _repoRefacciones.ReloadAsync();

        List<Refaccion> refacciones =
            (await _repoRefacciones.GetAllAsync()).ToList();


        // -----------------------------------------------------
        // 3. VALIDAR PRODUCTOS Y CALCULAR TOTAL
        // -----------------------------------------------------

        decimal total = 0m;

        foreach (DetalleVenta linea in lineas)
        {
            if (linea.Cantidad <= 0)
            {
                throw new InvalidOperationException(
                    "La cantidad de los productos debe ser mayor que cero."
                );
            }

            Refaccion? refaccion =
                refacciones.FirstOrDefault(
                    r => r.Id == linea.RefaccionId
                );

            if (refaccion == null)
            {
                throw new InvalidOperationException(
                    $"La refacción con ID {linea.RefaccionId} no existe."
                );
            }

            if (!refaccion.Activo)
            {
                throw new InvalidOperationException(
                    $"La refacción \"{refaccion.Nombre}\" no está disponible."
                );
            }

            if (refaccion.Stock < linea.Cantidad)
            {
                throw new InvalidOperationException(
                    $"No hay suficiente existencia de \"{refaccion.Nombre}\"."
                );
            }

            if (refaccion.Precio < 0)
            {
                throw new InvalidOperationException(
                    $"La refacción \"{refaccion.Nombre}\" tiene un precio inválido."
                );
            }

            // IMPORTANTE:
            // El precio se obtiene del inventario real,
            // no del precio que venga desde la interfaz.
            total += refaccion.Precio * linea.Cantidad;
        }


        // -----------------------------------------------------
        // 4. VALIDAR PAGO
        // -----------------------------------------------------

        if (total <= 0)
        {
            throw new InvalidOperationException(
                "El total de la venta debe ser mayor que cero."
            );
        }

        decimal cambio;

        if (metodoPago.Equals(
            "Efectivo",
            StringComparison.OrdinalIgnoreCase))
        {
            if (recibido < total)
            {
                throw new InvalidOperationException(
                    "La cantidad recibida es menor al total de la venta."
                );
            }

            cambio = recibido - total;
        }
        else
        {
            recibido = total;
            cambio = 0m;
        }


        // -----------------------------------------------------
        // 5. CREAR VENTA
        // -----------------------------------------------------

        Venta venta = new()
        {
            Folio = GenerarFolio(),
            Fecha = DateTime.Now,
            UsuarioId = usuario.Id,
            MetodoPago = metodoPago,
            Referencia = string.Empty,
            Recibido = recibido,
            Cambio = cambio,
            Total = total
        };


        // -----------------------------------------------------
        // 6. CREAR RESPALDO DE TRANSACCIÓN
        // -----------------------------------------------------

        string? carpetaRespaldo = null;

        try
        {
            carpetaRespaldo =
                JsonRepository<Venta>.CrearRespaldoTransaccion(
                    _repoVentas.CarpetaData
                );


            // -------------------------------------------------
            // 7. GUARDAR VENTA
            // -------------------------------------------------

            await _repoVentas.AddAsync(venta);


            // -------------------------------------------------
            // 8. GUARDAR DETALLES
            // -------------------------------------------------

            foreach (DetalleVenta lineaTicket in lineas)
            {
                Refaccion refaccion =
                    refacciones.First(
                        r => r.Id == lineaTicket.RefaccionId
                    );

                DetalleVenta detalle = new()
                {
                    VentaId = venta.Id,
                    RefaccionId = refaccion.Id,
                    Cantidad = lineaTicket.Cantidad,

                    // El precio válido sale del inventario.
                    PrecioUnitario = refaccion.Precio,

                    Refaccion = refaccion
                };

                await _repoDetalleVentas.AddAsync(detalle);

                venta.Lineas.Add(detalle);
            }

            await _repoVentas.UpdateAsync(venta);


            // -------------------------------------------------
            // 9. DESCONTAR INVENTARIO
            // -------------------------------------------------

            foreach (DetalleVenta linea in lineas)
            {
                Refaccion refaccion =
                    refacciones.First(
                        r => r.Id == linea.RefaccionId
                    );

                refaccion.Stock -= linea.Cantidad;

                if (refaccion.Stock <= 0)
                {
                    refaccion.Stock = 0;
                    refaccion.StockBajo = true;
                    refaccion.Activo = false;
                }
                else
                {
                    refaccion.StockBajo =
                        refaccion.Stock <= 5;

                    refaccion.Activo = true;
                }

                await _repoRefacciones.UpdateAsync(refaccion);
            }


            // -------------------------------------------------
            // 10. VENTA COMPLETADA
            // -------------------------------------------------

            JsonRepository<Venta>.EliminarRespaldoTransaccion(
                carpetaRespaldo
            );

            carpetaRespaldo = null;

            return venta;
        }
        catch
        {
            // -------------------------------------------------
            // 11. ROLLBACK
            // -------------------------------------------------

            if (carpetaRespaldo != null)
            {
                JsonRepository<Venta>.RestaurarRespaldoTransaccion(
                    _repoVentas.CarpetaData,
                    carpetaRespaldo
                );

                await _repoVentas.ReloadAsync();
                await _repoDetalleVentas.ReloadAsync();
                await _repoRefacciones.ReloadAsync();

                JsonRepository<Venta>.EliminarRespaldoTransaccion(
                    carpetaRespaldo
                );
            }

            throw;
        }
    }


    // =========================================================
    // GENERAR FOLIO
    // =========================================================

    private static string GenerarFolio()
    {
        return $"V-{DateTime.Now:yyyyMMdd-HHmmssfff}";
    }
}