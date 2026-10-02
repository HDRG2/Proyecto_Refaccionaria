using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Services;

public class ProductoService
{
    private readonly IRepository<Refaccion> _repoRefacciones;


    public ProductoService(
        IRepository<Refaccion> repoRefacciones)
    {
        _repoRefacciones = repoRefacciones
            ?? throw new ArgumentNullException(nameof(repoRefacciones));
    }


    // =========================================================
    // CREAR PRODUCTO
    // =========================================================

    public async Task<Refaccion> CrearProductoAsync(
        string nombre,
        string codigo,
        Categoria categoria,
        Marca marca,
        decimal precio,
        int stock,
        bool esUniversal,
        IEnumerable<int>? autosCompatibles)
    {
        // -----------------------------------------------------
        // 1. VALIDAR DATOS
        // -----------------------------------------------------

        nombre = nombre?.Trim() ?? string.Empty;
        codigo = codigo?.Trim() ?? string.Empty;

        if (string.IsNullOrWhiteSpace(nombre))
        {
            throw new InvalidOperationException(
                "El nombre del producto es obligatorio."
            );
        }

        if (string.IsNullOrWhiteSpace(codigo))
        {
            throw new InvalidOperationException(
                "El código del producto es obligatorio."
            );
        }

        if (categoria == null)
        {
            throw new InvalidOperationException(
                "La categoría es obligatoria."
            );
        }

        if (marca == null)
        {
            throw new InvalidOperationException(
                "La marca es obligatoria."
            );
        }

        if (precio < 0)
        {
            throw new InvalidOperationException(
                "El precio no puede ser negativo."
            );
        }

        if (stock < 0)
        {
            throw new InvalidOperationException(
                "El stock no puede ser negativo."
            );
        }


        // -----------------------------------------------------
        // 2. CONSULTAR DATOS REALES
        // -----------------------------------------------------

        await _repoRefacciones.ReloadAsync();

        List<Refaccion> productos =
            (await _repoRefacciones.GetAllAsync())
            .ToList();


        // -----------------------------------------------------
        // 3. EVITAR CÓDIGOS DUPLICADOS
        // -----------------------------------------------------

        bool codigoExiste =
            productos.Any(
                r => r.Codigo.Equals(
                    codigo,
                    StringComparison.OrdinalIgnoreCase
                )
            );

        if (codigoExiste)
        {
            throw new InvalidOperationException(
                "Ya existe una refacción con ese código."
            );
        }


        // -----------------------------------------------------
        // 4. PREPARAR AUTOS COMPATIBLES
        // -----------------------------------------------------

        List<int> autos =
            autosCompatibles?
                .Distinct()
                .ToList()
            ?? new List<int>();

        if (esUniversal)
        {
            autos.Clear();
        }


        // -----------------------------------------------------
        // 5. CREAR PRODUCTO
        // -----------------------------------------------------

        Refaccion producto = new()
        {
            Nombre = nombre,
            Codigo = codigo,

            CategoriaId = categoria.Id,
            MarcaId = marca.Id,

            CategoriaNombre = categoria.Nombre,
            MarcaNombre = marca.Nombre,

            Precio = precio,
            Stock = stock,

            StockBajo = stock <= 5,
            Activo = true,

            EsUniversal = esUniversal,
            AutosCompatibles = autos
        };


        // -----------------------------------------------------
        // 6. GUARDAR
        // -----------------------------------------------------

        await _repoRefacciones.AddAsync(producto);

        return producto;
    }


    // =========================================================
    // EDITAR PRODUCTO
    // =========================================================

    public async Task<Refaccion> EditarProductoAsync(
        Refaccion producto,
        string nombre,
        string codigo,
        Categoria categoria,
        Marca marca,
        decimal precio,
        int stock,
        bool esUniversal,
        IEnumerable<int>? autosCompatibles)
    {
        if (producto == null)
        {
            throw new InvalidOperationException(
                "No se encontró el producto que se desea editar."
            );
        }

        nombre = nombre?.Trim() ?? string.Empty;
        codigo = codigo?.Trim() ?? string.Empty;


        // -----------------------------------------------------
        // 1. VALIDACIONES
        // -----------------------------------------------------

        if (string.IsNullOrWhiteSpace(nombre))
        {
            throw new InvalidOperationException(
                "El nombre del producto es obligatorio."
            );
        }

        if (string.IsNullOrWhiteSpace(codigo))
        {
            throw new InvalidOperationException(
                "El código del producto es obligatorio."
            );
        }

        if (categoria == null)
        {
            throw new InvalidOperationException(
                "La categoría es obligatoria."
            );
        }

        if (marca == null)
        {
            throw new InvalidOperationException(
                "La marca es obligatoria."
            );
        }

        if (precio < 0)
        {
            throw new InvalidOperationException(
                "El precio no puede ser negativo."
            );
        }

        if (stock < 0)
        {
            throw new InvalidOperationException(
                "El stock no puede ser negativo."
            );
        }


        // -----------------------------------------------------
        // 2. CONSULTAR DATOS REALES
        // -----------------------------------------------------

        await _repoRefacciones.ReloadAsync();

        List<Refaccion> productos =
            (await _repoRefacciones.GetAllAsync())
            .ToList();


        // -----------------------------------------------------
        // 3. COMPROBAR QUE EL PRODUCTO SIGUE EXISTIENDO
        // -----------------------------------------------------

        Refaccion? productoReal =
            productos.FirstOrDefault(
                r => r.Id == producto.Id
            );

        if (productoReal == null)
        {
            throw new InvalidOperationException(
                "El producto ya no existe en el inventario."
            );
        }


        // -----------------------------------------------------
        // 4. EVITAR CÓDIGO DUPLICADO
        // -----------------------------------------------------

        bool codigoExiste =
            productos.Any(
                r =>
                    r.Id != productoReal.Id &&
                    r.Codigo.Equals(
                        codigo,
                        StringComparison.OrdinalIgnoreCase
                    )
            );

        if (codigoExiste)
        {
            throw new InvalidOperationException(
                "Ya existe otra refacción con ese código."
            );
        }


        // -----------------------------------------------------
        // 5. AUTOS COMPATIBLES
        // -----------------------------------------------------

        List<int> autos =
            autosCompatibles?
                .Distinct()
                .ToList()
            ?? new List<int>();

        if (esUniversal)
        {
            autos.Clear();
        }


        // -----------------------------------------------------
        // 6. MODIFICAR PRODUCTO REAL
        // -----------------------------------------------------

        productoReal.Nombre = nombre;
        productoReal.Codigo = codigo;

        productoReal.CategoriaId = categoria.Id;
        productoReal.MarcaId = marca.Id;

        productoReal.CategoriaNombre = categoria.Nombre;
        productoReal.MarcaNombre = marca.Nombre;

        productoReal.Precio = precio;
        productoReal.Stock = stock;

        productoReal.StockBajo =
            stock <= 5;

        productoReal.EsUniversal =
            esUniversal;

        productoReal.AutosCompatibles =
            autos;


        // -----------------------------------------------------
        // 7. GUARDAR
        // -----------------------------------------------------

        await _repoRefacciones.UpdateAsync(
            productoReal
        );

        return productoReal;
    }


    // =========================================================
    // RETIRAR PRODUCTO
    // =========================================================

    public async Task RetirarProductoAsync(
        int productoId)
    {
        Refaccion producto =
            await ObtenerProductoRealAsync(productoId);

        producto.Activo = false;

        await _repoRefacciones.UpdateAsync(
            producto
        );
    }


    // =========================================================
    // REACTIVAR / REABASTECER
    // =========================================================

    public async Task<Refaccion> ReactivarProductoAsync(
        int productoId,
        int cantidadRecibida)
    {
        if (cantidadRecibida < 0)
        {
            throw new InvalidOperationException(
                "La cantidad recibida no puede ser negativa."
            );
        }

        Refaccion producto =
            await ObtenerProductoRealAsync(productoId);

        if (producto.Stock >
            int.MaxValue - cantidadRecibida)
        {
            throw new InvalidOperationException(
                "La cantidad excede el límite permitido de inventario."
            );
        }

        producto.Stock += cantidadRecibida;

        producto.Activo = true;

        producto.StockBajo =
            producto.Stock <= 5;

        await _repoRefacciones.UpdateAsync(
            producto
        );

        return producto;
    }


    // =========================================================
    // ELIMINAR DEFINITIVAMENTE
    // =========================================================

    public async Task EliminarProductoAsync(
        int productoId)
    {
        Refaccion producto =
            await ObtenerProductoRealAsync(productoId);

        await _repoRefacciones.DeleteAsync(
            producto.Id
        );
    }


    // =========================================================
    // OBTENER PRODUCTO REAL
    // =========================================================

    private async Task<Refaccion> ObtenerProductoRealAsync(
        int productoId)
    {
        if (productoId <= 0)
        {
            throw new InvalidOperationException(
                "El identificador del producto no es válido."
            );
        }

        await _repoRefacciones.ReloadAsync();

        Refaccion? producto =
            (await _repoRefacciones.GetAllAsync())
            .FirstOrDefault(
                r => r.Id == productoId
            );

        if (producto == null)
        {
            throw new InvalidOperationException(
                "El producto ya no existe en el inventario."
            );
        }

        return producto;
    }
}