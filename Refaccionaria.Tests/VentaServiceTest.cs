using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

using Xunit;

namespace Refaccionaria.Tests;

public class VentaServiceTests
{
    [Fact]
    public async Task RegistrarVenta_DebeGuardarVentaDetalleYDescontarStock()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaVentas =
            Path.Combine(
                carpetaData,
                "ventas.json"
            );

        string rutaDetalles =
            Path.Combine(
                carpetaData,
                "detalleVentas.json"
            );

        string rutaRefacciones =
            Path.Combine(
                carpetaData,
                "refacciones.json"
            );

        // Los tres archivos deben existir porque participan
        // en el respaldo de transacción.
        await File.WriteAllTextAsync(
            rutaVentas,
            "[]"
        );

        await File.WriteAllTextAsync(
            rutaDetalles,
            "[]"
        );

        await File.WriteAllTextAsync(
            rutaRefacciones,
            "[]"
        );

        try
        {
            // =============================================
            // REPOSITORIOS TEMPORALES
            // =============================================

            JsonRepository<Venta> repoVentas =
                new(rutaVentas);

            JsonRepository<DetalleVenta> repoDetalles =
                new(rutaDetalles);

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);


            // =============================================
            // SERVICIO
            // =============================================

            VentaService ventaService =
                new(
                    repoVentas,
                    repoDetalles,
                    repoRefacciones
                );


            // =============================================
            // CREAR PRODUCTO EN INVENTARIO
            //
            // Precio real = $150
            // Stock inicial = 10
            // =============================================

            Refaccion producto = new()
            {
                Codigo = "FILTRO-001",
                Nombre = "Filtro de aceite",
                Precio = 150m,
                Stock = 10,
                StockBajo = false,
                Activo = true,
                EsUniversal = true
            };

            await repoRefacciones.AddAsync(
                producto
            );


            // =============================================
            // USUARIO QUE REALIZA LA VENTA
            // =============================================

            Usuario usuario = new()
            {
                Id = 20,
                Nombre = "Pedro Lopez",
                NombreUsuario = "P201",
                Rol = "Vendedor",
                Activo = true
            };


            // =============================================
            // LÍNEA DEL TICKET
            //
            // Vendemos 2 unidades.
            //
            // IMPORTANTE:
            // ponemos PrecioUnitario = 1 a propósito.
            // VentaService NO debe confiar en ese precio.
            // Debe usar los $150 del inventario.
            // =============================================

            DetalleVenta linea = new()
            {
                RefaccionId = producto.Id,
                Cantidad = 2,
                PrecioUnitario = 1m
            };


            // =============================================
            // REGISTRAR VENTA
            //
            // 2 x $150 = $300
            // Recibimos $500
            // Cambio esperado = $200
            // =============================================

            Venta venta =
                await ventaService.RegistrarVentaAsync(
                    usuario,
                    new[] { linea },
                    "Efectivo",
                    500m
                );


            // =============================================
            // COMPROBAR RESULTADO DEVUELTO
            // =============================================

            Assert.True(
                venta.Id > 0
            );

            Assert.Equal(
                usuario.Id,
                venta.UsuarioId
            );

            Assert.Equal(
                300m,
                venta.Total
            );

            Assert.Equal(
                500m,
                venta.Recibido
            );

            Assert.Equal(
                200m,
                venta.Cambio
            );

            Assert.Equal(
                "Efectivo",
                venta.MetodoPago
            );


            // =============================================
            // COMPROBAR ventas.json
            // =============================================

            await repoVentas.ReloadAsync();

            var ventas =
                (await repoVentas.GetAllAsync())
                .ToList();

            Assert.Single(
                ventas
            );

            Assert.Equal(
                300m,
                ventas[0].Total
            );

            Assert.Equal(
                usuario.Id,
                ventas[0].UsuarioId
            );


            // =============================================
            // COMPROBAR detalleVentas.json
            // =============================================

            await repoDetalles.ReloadAsync();

            var detalles =
                (await repoDetalles.GetAllAsync())
                .ToList();

            Assert.Single(
                detalles
            );

            Assert.Equal(
                venta.Id,
                detalles[0].VentaId
            );

            Assert.Equal(
                producto.Id,
                detalles[0].RefaccionId
            );

            Assert.Equal(
                2,
                detalles[0].Cantidad
            );

            // Debe haber usado el precio REAL del inventario.
            Assert.Equal(
                150m,
                detalles[0].PrecioUnitario
            );


            // =============================================
            // COMPROBAR INVENTARIO
            //
            // Stock inicial 10
            // Venta 2
            // Stock final 8
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion productoFinal =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);

            Assert.Equal(
                8,
                productoFinal.Stock
            );

            Assert.True(
                productoFinal.Activo
            );

            Assert.False(
                productoFinal.StockBajo
            );
        }
        finally
        {
            if (Directory.Exists(carpetaTemporal))
            {
                Directory.Delete(
                    carpetaTemporal,
                    recursive: true
                );
            }
        }
    }

    [Fact]
    public async Task RegistrarVenta_NoDebePermitirStockInsuficiente()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaVentas =
            Path.Combine(carpetaData, "ventas.json");

        string rutaDetalles =
            Path.Combine(carpetaData, "detalleVentas.json");

        string rutaRefacciones =
            Path.Combine(carpetaData, "refacciones.json");


        await File.WriteAllTextAsync(rutaVentas, "[]");
        await File.WriteAllTextAsync(rutaDetalles, "[]");
        await File.WriteAllTextAsync(rutaRefacciones, "[]");


        try
        {
            // =============================================
            // REPOSITORIOS Y SERVICIO
            // =============================================

            JsonRepository<Venta> repoVentas =
                new(rutaVentas);

            JsonRepository<DetalleVenta> repoDetalles =
                new(rutaDetalles);

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            VentaService ventaService =
                new(
                    repoVentas,
                    repoDetalles,
                    repoRefacciones
                );


            // =============================================
            // PRODUCTO CON SOLO 3 UNIDADES
            // =============================================

            Refaccion producto = new()
            {
                Codigo = "FILTRO-001",
                Nombre = "Filtro de aceite",
                Precio = 150m,
                Stock = 3,
                StockBajo = true,
                Activo = true,
                EsUniversal = true
            };

            await repoRefacciones.AddAsync(producto);


            // =============================================
            // USUARIO ACTIVO
            // =============================================

            Usuario usuario = new()
            {
                Id = 20,
                Nombre = "Pedro Lopez",
                NombreUsuario = "P201",
                Rol = "Vendedor",
                Activo = true
            };


            // =============================================
            // INTENTAMOS VENDER 5
            //
            // Stock disponible = 3
            // Cantidad solicitada = 5
            // =============================================

            DetalleVenta linea = new()
            {
                RefaccionId = producto.Id,
                Cantidad = 5,
                PrecioUnitario = 150m
            };


            // =============================================
            // LA VENTA DEBE SER RECHAZADA
            // =============================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await ventaService.RegistrarVentaAsync(
                            usuario,
                            new[] { linea },
                            "Efectivo",
                            1000m
                        )
                );


            Assert.Equal(
                "No hay suficiente existencia de \"Filtro de aceite\".",
                error.Message
            );


            // =============================================
            // NO DEBE EXISTIR NINGUNA VENTA
            // =============================================

            await repoVentas.ReloadAsync();

            var ventas =
                (await repoVentas.GetAllAsync())
                .ToList();

            Assert.Empty(ventas);


            // =============================================
            // NO DEBE EXISTIR NINGÚN DETALLE
            // =============================================

            await repoDetalles.ReloadAsync();

            var detalles =
                (await repoDetalles.GetAllAsync())
                .ToList();

            Assert.Empty(detalles);


            // =============================================
            // EL STOCK DEBE SEGUIR EXACTAMENTE EN 3
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion productoFinal =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);

            Assert.Equal(
                3,
                productoFinal.Stock
            );

            Assert.True(
                productoFinal.Activo
            );
        }
        finally
        {
            if (Directory.Exists(carpetaTemporal))
            {
                Directory.Delete(
                    carpetaTemporal,
                    recursive: true
                );
            }
        }
    }

    [Fact]
    public async Task RegistrarVenta_NoDebePermitirPagoInsuficienteEnEfectivo()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaVentas =
            Path.Combine(carpetaData, "ventas.json");

        string rutaDetalles =
            Path.Combine(carpetaData, "detalleVentas.json");

        string rutaRefacciones =
            Path.Combine(carpetaData, "refacciones.json");

        await File.WriteAllTextAsync(rutaVentas, "[]");
        await File.WriteAllTextAsync(rutaDetalles, "[]");
        await File.WriteAllTextAsync(rutaRefacciones, "[]");

        try
        {
            // =============================================
            // REPOSITORIOS Y SERVICIO
            // =============================================

            JsonRepository<Venta> repoVentas =
                new(rutaVentas);

            JsonRepository<DetalleVenta> repoDetalles =
                new(rutaDetalles);

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            VentaService ventaService =
                new(
                    repoVentas,
                    repoDetalles,
                    repoRefacciones
                );


            // =============================================
            // PRODUCTO
            //
            // Precio = $150
            // Vendemos 2
            // Total = $300
            // =============================================

            Refaccion producto = new()
            {
                Codigo = "FILTRO-001",
                Nombre = "Filtro de aceite",
                Precio = 150m,
                Stock = 10,
                StockBajo = false,
                Activo = true,
                EsUniversal = true
            };

            await repoRefacciones.AddAsync(producto);


            // =============================================
            // USUARIO
            // =============================================

            Usuario usuario = new()
            {
                Id = 20,
                Nombre = "Pedro Lopez",
                NombreUsuario = "P201",
                Rol = "Vendedor",
                Activo = true
            };


            // =============================================
            // TICKET
            // =============================================

            DetalleVenta linea = new()
            {
                RefaccionId = producto.Id,
                Cantidad = 2,
                PrecioUnitario = 150m
            };


            // =============================================
            // INTENTAR PAGAR
            //
            // Total = $300
            // Recibido = $200
            // =============================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await ventaService.RegistrarVentaAsync(
                            usuario,
                            new[] { linea },
                            "Efectivo",
                            200m
                        )
                );


            // =============================================
            // COMPROBAR ERROR
            // =============================================

            Assert.Equal(
                "La cantidad recibida es menor al total de la venta.",
                error.Message
            );


            // =============================================
            // NO DEBE GUARDARSE LA VENTA
            // =============================================

            await repoVentas.ReloadAsync();

            var ventas =
                (await repoVentas.GetAllAsync())
                .ToList();

            Assert.Empty(ventas);


            // =============================================
            // NO DEBE GUARDARSE NINGÚN DETALLE
            // =============================================

            await repoDetalles.ReloadAsync();

            var detalles =
                (await repoDetalles.GetAllAsync())
                .ToList();

            Assert.Empty(detalles);


            // =============================================
            // EL INVENTARIO NO DEBE CAMBIAR
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion productoFinal =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);

            Assert.Equal(
                10,
                productoFinal.Stock
            );

            Assert.True(
                productoFinal.Activo
            );
        }
        finally
        {
            if (Directory.Exists(carpetaTemporal))
            {
                Directory.Delete(
                    carpetaTemporal,
                    recursive: true
                );
            }
        }
    }

    [Fact]
    public async Task RegistrarVenta_DebeDesactivarProductoCuandoStockLlegaACero()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaVentas =
            Path.Combine(carpetaData, "ventas.json");

        string rutaDetalles =
            Path.Combine(carpetaData, "detalleVentas.json");

        string rutaRefacciones =
            Path.Combine(carpetaData, "refacciones.json");

        await File.WriteAllTextAsync(rutaVentas, "[]");
        await File.WriteAllTextAsync(rutaDetalles, "[]");
        await File.WriteAllTextAsync(rutaRefacciones, "[]");

        try
        {
            // =============================================
            // REPOSITORIOS Y SERVICIO
            // =============================================

            JsonRepository<Venta> repoVentas =
                new(rutaVentas);

            JsonRepository<DetalleVenta> repoDetalles =
                new(rutaDetalles);

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            VentaService ventaService =
                new(
                    repoVentas,
                    repoDetalles,
                    repoRefacciones
                );


            // =============================================
            // PRODUCTO CON STOCK 3
            // =============================================

            Refaccion producto = new()
            {
                Codigo = "FILTRO-001",
                Nombre = "Filtro de aceite",
                Precio = 100m,
                Stock = 3,
                StockBajo = true,
                Activo = true,
                EsUniversal = true
            };

            await repoRefacciones.AddAsync(producto);


            // =============================================
            // USUARIO
            // =============================================

            Usuario usuario = new()
            {
                Id = 20,
                Nombre = "Pedro Lopez",
                NombreUsuario = "P201",
                Rol = "Vendedor",
                Activo = true
            };


            // =============================================
            // VENDER EXACTAMENTE LAS 3 UNIDADES
            // =============================================

            DetalleVenta linea = new()
            {
                RefaccionId = producto.Id,
                Cantidad = 3,
                PrecioUnitario = 100m
            };

            Venta venta =
                await ventaService.RegistrarVentaAsync(
                    usuario,
                    new[] { linea },
                    "Efectivo",
                    300m
                );


            // =============================================
            // LA VENTA DEBE SER CORRECTA
            // =============================================

            Assert.True(
                venta.Id > 0
            );

            Assert.Equal(
                300m,
                venta.Total
            );

            Assert.Equal(
                0m,
                venta.Cambio
            );


            // =============================================
            // RECARGAR INVENTARIO DESDE JSON
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion productoFinal =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);


            // =============================================
            // COMPROBAR PRODUCTO AGOTADO
            // =============================================

            Assert.Equal(
                0,
                productoFinal.Stock
            );

            Assert.True(
                productoFinal.StockBajo
            );

            Assert.False(
                productoFinal.Activo
            );


            // =============================================
            // LA VENTA Y EL DETALLE DEBEN EXISTIR
            // =============================================

            await repoVentas.ReloadAsync();

            var ventas =
                (await repoVentas.GetAllAsync())
                .ToList();

            Assert.Single(
                ventas
            );


            await repoDetalles.ReloadAsync();

            var detalles =
                (await repoDetalles.GetAllAsync())
                .ToList();

            Assert.Single(
                detalles
            );

            Assert.Equal(
                3,
                detalles[0].Cantidad
            );

            Assert.Equal(
                100m,
                detalles[0].PrecioUnitario
            );
        }
        finally
        {
            if (Directory.Exists(carpetaTemporal))
            {
                Directory.Delete(
                    carpetaTemporal,
                    recursive: true
                );
            }
        }
    }

    [Fact]
    public async Task Rollback_DebeRestaurarLosTresArchivosDeLaVenta()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaVentas =
            Path.Combine(carpetaData, "ventas.json");

        string rutaDetalles =
            Path.Combine(carpetaData, "detalleVentas.json");

        string rutaRefacciones =
            Path.Combine(carpetaData, "refacciones.json");

        try
        {
            // =============================================
            // ESTADO ORIGINAL
            // =============================================

            string ventasOriginal =
                """
            [
              {
                "Id": 1,
                "Folio": "VENTA-ORIGINAL"
              }
            ]
            """;

            string detallesOriginal =
                """
            [
              {
                "Id": 1,
                "VentaId": 1,
                "RefaccionId": 1,
                "Cantidad": 2,
                "PrecioUnitario": 100
              }
            ]
            """;

            string refaccionesOriginal =
                """
            [
              {
                "Id": 1,
                "Codigo": "PROD-001",
                "Nombre": "Producto original",
                "Precio": 100,
                "Stock": 10,
                "Activo": true
              }
            ]
            """;

            await File.WriteAllTextAsync(
                rutaVentas,
                ventasOriginal
            );

            await File.WriteAllTextAsync(
                rutaDetalles,
                detallesOriginal
            );

            await File.WriteAllTextAsync(
                rutaRefacciones,
                refaccionesOriginal
            );


            // =============================================
            // CREAR RESPALDO DE TRANSACCIÓN
            // =============================================

            string carpetaRespaldo =
                JsonRepository<Venta>
                    .CrearRespaldoTransaccion(
                        carpetaData
                    );


            Assert.True(
                Directory.Exists(carpetaRespaldo)
            );


            // =============================================
            // SIMULAR UNA VENTA QUE QUEDÓ A MEDIAS
            //
            // Modificamos intencionalmente los 3 archivos.
            // =============================================

            await File.WriteAllTextAsync(
                rutaVentas,
                """
            [
              {
                "Id": 999,
                "Folio": "VENTA-DAÑADA"
              }
            ]
            """
            );

            await File.WriteAllTextAsync(
                rutaDetalles,
                """
            [
              {
                "Id": 999,
                "VentaId": 999,
                "RefaccionId": 1,
                "Cantidad": 999,
                "PrecioUnitario": 1
              }
            ]
            """
            );

            await File.WriteAllTextAsync(
                rutaRefacciones,
                """
            [
              {
                "Id": 1,
                "Codigo": "PROD-001",
                "Nombre": "Producto original",
                "Precio": 100,
                "Stock": 0,
                "Activo": false
              }
            ]
            """
            );


            // =============================================
            // COMPROBAR QUE REALMENTE CAMBIARON
            // =============================================

            Assert.NotEqual(
                ventasOriginal,
                await File.ReadAllTextAsync(rutaVentas)
            );

            Assert.NotEqual(
                detallesOriginal,
                await File.ReadAllTextAsync(rutaDetalles)
            );

            Assert.NotEqual(
                refaccionesOriginal,
                await File.ReadAllTextAsync(rutaRefacciones)
            );


            // =============================================
            // EJECUTAR ROLLBACK
            // =============================================

            JsonRepository<Venta>
                .RestaurarRespaldoTransaccion(
                    carpetaData,
                    carpetaRespaldo
                );


            // =============================================
            // LEER ARCHIVOS RESTAURADOS
            // =============================================

            string ventasRestauradas =
                await File.ReadAllTextAsync(
                    rutaVentas
                );

            string detallesRestaurados =
                await File.ReadAllTextAsync(
                    rutaDetalles
                );

            string refaccionesRestauradas =
                await File.ReadAllTextAsync(
                    rutaRefacciones
                );


            // =============================================
            // DEBEN SER EXACTAMENTE IGUALES
            // AL ESTADO ANTERIOR
            // =============================================

            Assert.Equal(
                ventasOriginal,
                ventasRestauradas
            );

            Assert.Equal(
                detallesOriginal,
                detallesRestaurados
            );

            Assert.Equal(
                refaccionesOriginal,
                refaccionesRestauradas
            );


            // =============================================
            // ELIMINAR RESPALDO TEMPORAL
            // =============================================

            JsonRepository<Venta>
                .EliminarRespaldoTransaccion(
                    carpetaRespaldo
                );


            // Ya no debe existir.
            Assert.False(
                Directory.Exists(carpetaRespaldo)
            );
        }
        finally
        {
            if (Directory.Exists(carpetaTemporal))
            {
                Directory.Delete(
                    carpetaTemporal,
                    recursive: true
                );
            }
        }
    }
}