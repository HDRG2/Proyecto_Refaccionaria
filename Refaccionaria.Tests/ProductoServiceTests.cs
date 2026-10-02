using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

using Xunit;

namespace Refaccionaria.Tests;

public class ProductoServiceTests
{
    [Fact]
    public async Task CrearProducto_NoDebePermitirCodigoDuplicado()
    {
        // =================================================
        // 1. CREAR CARPETA TEMPORAL
        // =================================================

        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        Directory.CreateDirectory(carpetaTemporal);

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaRefacciones =
            Path.Combine(
                carpetaData,
                "refacciones.json"
            );

        await File.WriteAllTextAsync(
            rutaRefacciones,
            "[]"
        );


        try
        {
            // =================================================
            // 2. CREAR REPOSITORIO Y SERVICIO TEMPORALES
            // =================================================

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            ProductoService productoService =
                new(repoRefacciones);


            // =================================================
            // 3. DATOS DE CATEGORÍA Y MARCA
            // =================================================

            Categoria categoria = new()
            {
                Id = 1,
                Nombre = "Filtros"
            };

            Marca marca = new()
            {
                Id = 1,
                Nombre = "Bosch"
            };


            // =================================================
            // 4. CREAR PRIMER PRODUCTO
            // =================================================

            Refaccion producto =
                await productoService.CrearProductoAsync(
                    "Filtro de aceite",
                    "PRUEBA-001",
                    categoria,
                    marca,
                    150m,
                    10,
                    true,
                    null
                );


            Assert.True(
                producto.Id > 0
            );

            Assert.Equal(
                "PRUEBA-001",
                producto.Codigo
            );


            // =================================================
            // 5. INTENTAR CREAR OTRO CON EL MISMO CÓDIGO
            //
            // Lo ponemos en minúsculas a propósito.
            // =================================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await productoService.CrearProductoAsync(
                            "Otro filtro",
                            "prueba-001",
                            categoria,
                            marca,
                            200m,
                            20,
                            true,
                            null
                        )
                );


            // =================================================
            // 6. COMPROBAR EL MENSAJE
            // =================================================

            Assert.Equal(
                "Ya existe una refacción con ese código.",
                error.Message
            );


            // =================================================
            // 7. RECARGAR DESDE EL JSON
            // =================================================

            await repoRefacciones.ReloadAsync();

            var productos =
                (await repoRefacciones.GetAllAsync())
                .ToList();


            // =================================================
            // 8. SOLO DEBE EXISTIR EL PRIMER PRODUCTO
            // =================================================

            Assert.Single(
                productos
            );

            Assert.Equal(
                "PRUEBA-001",
                productos[0].Codigo
            );

            Assert.Equal(
                "Filtro de aceite",
                productos[0].Nombre
            );
        }
        finally
        {
            // =================================================
            // 9. ELIMINAR DATOS TEMPORALES
            // =================================================

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
    public async Task EditarProducto_NoDebePermitirCodigoDeOtroProducto()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        Directory.CreateDirectory(carpetaTemporal);

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaRefacciones =
            Path.Combine(
                carpetaData,
                "refacciones.json"
            );

        await File.WriteAllTextAsync(
            rutaRefacciones,
            "[]"
        );

        try
        {
            // =============================================
            // CREAR REPOSITORIO Y SERVICIO
            // =============================================

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            ProductoService productoService =
                new(repoRefacciones);


            // =============================================
            // CATEGORÍA Y MARCA
            // =============================================

            Categoria categoria = new()
            {
                Id = 1,
                Nombre = "Filtros"
            };

            Marca marca = new()
            {
                Id = 1,
                Nombre = "Bosch"
            };


            // =============================================
            // CREAR DOS PRODUCTOS
            // =============================================

            Refaccion filtroAceite =
                await productoService.CrearProductoAsync(
                    "Filtro de aceite",
                    "FILTRO-001",
                    categoria,
                    marca,
                    150m,
                    10,
                    true,
                    null
                );

            Refaccion filtroAire =
                await productoService.CrearProductoAsync(
                    "Filtro de aire",
                    "FILTRO-002",
                    categoria,
                    marca,
                    200m,
                    15,
                    true,
                    null
                );


            // =============================================
            // INTENTAR CAMBIAR EL CÓDIGO DEL SEGUNDO
            // =============================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await productoService.EditarProductoAsync(
                            filtroAire,
                            "Filtro de aire modificado",
                            "filtro-001",
                            categoria,
                            marca,
                            250m,
                            20,
                            true,
                            null
                        )
                );


            // =============================================
            // COMPROBAR EL MENSAJE
            // =============================================

            Assert.Equal(
                "Ya existe otra refacción con ese código.",
                error.Message
            );


            // =============================================
            // RECARGAR EL JSON
            // =============================================

            await repoRefacciones.ReloadAsync();

            var productos =
                (await repoRefacciones.GetAllAsync())
                .ToList();


            // =============================================
            // DEBEN SEGUIR EXISTIENDO SOLO LOS DOS
            // =============================================

            Assert.Equal(
                2,
                productos.Count
            );


            // =============================================
            // COMPROBAR PRIMER PRODUCTO
            // =============================================

            Refaccion primero =
                productos.Single(
                    p => p.Id == filtroAceite.Id
                );

            Assert.Equal(
                "FILTRO-001",
                primero.Codigo
            );


            // =============================================
            // COMPROBAR QUE EL SEGUNDO NO FUE MODIFICADO
            // =============================================

            Refaccion segundo =
                productos.Single(
                    p => p.Id == filtroAire.Id
                );

            Assert.Equal(
                "FILTRO-002",
                segundo.Codigo
            );

            Assert.Equal(
                "Filtro de aire",
                segundo.Nombre
            );

            Assert.Equal(
                200m,
                segundo.Precio
            );

            Assert.Equal(
                15,
                segundo.Stock
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
    public async Task Producto_DebePoderRetirarseYReactivarseConNuevoStock()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        Directory.CreateDirectory(carpetaTemporal);

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaRefacciones =
            Path.Combine(
                carpetaData,
                "refacciones.json"
            );

        await File.WriteAllTextAsync(
            rutaRefacciones,
            "[]"
        );

        try
        {
            // =============================================
            // CREAR REPOSITORIO Y SERVICIO
            // =============================================

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            ProductoService productoService =
                new(repoRefacciones);


            // =============================================
            // CATEGORÍA Y MARCA
            // =============================================

            Categoria categoria = new()
            {
                Id = 1,
                Nombre = "Filtros"
            };

            Marca marca = new()
            {
                Id = 1,
                Nombre = "Bosch"
            };


            // =============================================
            // CREAR PRODUCTO CON STOCK 12
            // =============================================

            Refaccion producto =
                await productoService.CrearProductoAsync(
                    "Filtro de aceite",
                    "FILTRO-001",
                    categoria,
                    marca,
                    150m,
                    12,
                    true,
                    null
                );

            Assert.True(producto.Activo);
            Assert.Equal(12, producto.Stock);


            // =============================================
            // RETIRAR PRODUCTO
            // =============================================

            await productoService.RetirarProductoAsync(
                producto.Id
            );


            // =============================================
            // COMPROBAR PRODUCTO RETIRADO
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion retirado =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);

            Assert.False(
                retirado.Activo
            );

            // Retirar NO debe modificar el stock.
            Assert.Equal(
                12,
                retirado.Stock
            );


            // =============================================
            // REACTIVAR Y AGREGAR 5 UNIDADES
            // =============================================

            Refaccion reactivado =
                await productoService.ReactivarProductoAsync(
                    producto.Id,
                    5
                );

            Assert.True(
                reactivado.Activo
            );

            Assert.Equal(
                17,
                reactivado.Stock
            );


            // =============================================
            // COMPROBAR DIRECTAMENTE EN EL JSON
            // =============================================

            await repoRefacciones.ReloadAsync();

            Refaccion productoFinal =
                (await repoRefacciones.GetAllAsync())
                .Single(p => p.Id == producto.Id);

            Assert.True(
                productoFinal.Activo
            );

            Assert.Equal(
                17,
                productoFinal.Stock
            );

            Assert.False(
                productoFinal.StockBajo
            );


            // =============================================
            // EL PRODUCTO DEBE SEGUIR EXISTIENDO
            // =============================================

            var productos =
                (await repoRefacciones.GetAllAsync())
                .ToList();

            Assert.Single(
                productos
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
    public async Task EliminarProducto_DebeEliminarloDefinitivamente()
    {
        string carpetaTemporal =
            Path.Combine(
                Path.GetTempPath(),
                "RefaccionariaTests",
                Guid.NewGuid().ToString()
            );

        Directory.CreateDirectory(carpetaTemporal);

        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(carpetaData);

        string rutaRefacciones =
            Path.Combine(
                carpetaData,
                "refacciones.json"
            );

        await File.WriteAllTextAsync(
            rutaRefacciones,
            "[]"
        );

        try
        {
            // =============================================
            // CREAR REPOSITORIO Y SERVICIO
            // =============================================

            JsonRepository<Refaccion> repoRefacciones =
                new(rutaRefacciones);

            ProductoService productoService =
                new(repoRefacciones);


            // =============================================
            // CATEGORÍA Y MARCA
            // =============================================

            Categoria categoria = new()
            {
                Id = 1,
                Nombre = "Filtros"
            };

            Marca marca = new()
            {
                Id = 1,
                Nombre = "Bosch"
            };


            // =============================================
            // CREAR PRODUCTO
            // =============================================

            Refaccion producto =
                await productoService.CrearProductoAsync(
                    "Filtro de aceite",
                    "FILTRO-001",
                    categoria,
                    marca,
                    150m,
                    12,
                    true,
                    null
                );


            // =============================================
            // COMPROBAR QUE EXISTE
            // =============================================

            await repoRefacciones.ReloadAsync();

            var productosAntes =
                (await repoRefacciones.GetAllAsync())
                .ToList();

            Assert.Single(productosAntes);

            Assert.Equal(
                producto.Id,
                productosAntes[0].Id
            );


            // =============================================
            // ELIMINAR DEFINITIVAMENTE
            // =============================================

            await productoService.EliminarProductoAsync(
                producto.Id
            );


            // =============================================
            // RECARGAR DESDE EL JSON
            // =============================================

            await repoRefacciones.ReloadAsync();

            var productosDespues =
                (await repoRefacciones.GetAllAsync())
                .ToList();


            // =============================================
            // YA NO DEBE EXISTIR
            // =============================================

            Assert.Empty(
                productosDespues
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