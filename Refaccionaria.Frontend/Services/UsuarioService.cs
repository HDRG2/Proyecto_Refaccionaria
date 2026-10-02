using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Services;

public class UsuarioService
{
    private readonly IRepository<Usuario> _repoUsuarios;


    public UsuarioService(
        IRepository<Usuario> repoUsuarios)
    {
        _repoUsuarios = repoUsuarios
            ?? throw new ArgumentNullException(nameof(repoUsuarios));
    }


    // =========================================================
    // CREAR EMPLEADO
    // =========================================================

    public async Task<Usuario> CrearEmpleadoAsync(
        string nombre,
        string telefono,
        string nombreUsuario,
        string password,
        bool activo)
    {
        nombre =
            nombre?.Trim() ?? string.Empty;

        telefono =
            telefono?.Trim() ?? string.Empty;

        nombreUsuario =
            nombreUsuario?.Trim() ?? string.Empty;

        password =
            password?.Trim() ?? string.Empty;


        // -----------------------------------------------------
        // VALIDAR NOMBRE
        // -----------------------------------------------------

        if (string.IsNullOrWhiteSpace(nombre))
        {
            throw new InvalidOperationException(
                "El nombre del empleado es obligatorio."
            );
        }


        // -----------------------------------------------------
        // VALIDAR TELÉFONO
        // -----------------------------------------------------

        ValidarTelefono(
            telefono
        );


        // -----------------------------------------------------
        // VALIDAR USUARIO
        // -----------------------------------------------------

        if (string.IsNullOrWhiteSpace(nombreUsuario))
        {
            throw new InvalidOperationException(
                "El nombre de usuario es obligatorio."
            );
        }


        // -----------------------------------------------------
        // VALIDAR CONTRASEÑA
        // -----------------------------------------------------

        if (string.IsNullOrWhiteSpace(password))
        {
            throw new InvalidOperationException(
                "La contraseña es obligatoria."
            );
        }


        // -----------------------------------------------------
        // CONSULTAR DATOS REALES
        // -----------------------------------------------------

        await _repoUsuarios.ReloadAsync();

        List<Usuario> usuarios =
            (await _repoUsuarios.GetAllAsync())
            .ToList();


        // -----------------------------------------------------
        // EVITAR USUARIO DUPLICADO
        // -----------------------------------------------------

        bool usuarioExiste =
            usuarios.Any(
                u =>
                    u.NombreUsuario.Equals(
                        nombreUsuario,
                        StringComparison.OrdinalIgnoreCase
                    )
            );

        if (usuarioExiste)
        {
            throw new InvalidOperationException(
                "Ya existe un empleado con ese nombre de usuario."
            );
        }


        // -----------------------------------------------------
        // CREAR EMPLEADO
        // -----------------------------------------------------

        Usuario empleado = new()
        {
            Nombre = nombre,
            Telefono = telefono,
            NombreUsuario = nombreUsuario,
            Password = password,

            Rol = "Vendedor",
            Activo = activo
        };


        // -----------------------------------------------------
        // GUARDAR
        // -----------------------------------------------------

        await _repoUsuarios.AddAsync(
            empleado
        );

        return empleado;
    }


    // =========================================================
    // EDITAR EMPLEADO
    // =========================================================

    public async Task<Usuario> EditarEmpleadoAsync(
        Usuario empleado,
        string nombre,
        string telefono,
        string nombreUsuario,
        string password,
        bool activo)
    {
        if (empleado == null)
        {
            throw new InvalidOperationException(
                "No se encontró el empleado que se desea editar."
            );
        }


        nombre =
            nombre?.Trim() ?? string.Empty;

        telefono =
            telefono?.Trim() ?? string.Empty;

        nombreUsuario =
            nombreUsuario?.Trim() ?? string.Empty;

        password =
            password?.Trim() ?? string.Empty;


        // -----------------------------------------------------
        // VALIDACIONES
        // -----------------------------------------------------

        if (string.IsNullOrWhiteSpace(nombre))
        {
            throw new InvalidOperationException(
                "El nombre del empleado es obligatorio."
            );
        }


        ValidarTelefono(
            telefono
        );


        if (string.IsNullOrWhiteSpace(nombreUsuario))
        {
            throw new InvalidOperationException(
                "El nombre de usuario es obligatorio."
            );
        }


        if (string.IsNullOrWhiteSpace(password))
        {
            throw new InvalidOperationException(
                "La contraseña es obligatoria."
            );
        }


        // -----------------------------------------------------
        // CONSULTAR DATOS REALES
        // -----------------------------------------------------

        await _repoUsuarios.ReloadAsync();

        List<Usuario> usuarios =
            (await _repoUsuarios.GetAllAsync())
            .ToList();


        // -----------------------------------------------------
        // COMPROBAR QUE SIGUE EXISTIENDO
        // -----------------------------------------------------

        Usuario? empleadoReal =
            usuarios.FirstOrDefault(
                u => u.Id == empleado.Id
            );


        if (empleadoReal == null)
        {
            throw new InvalidOperationException(
                "El empleado ya no existe."
            );
        }


        // -----------------------------------------------------
        // EVITAR USUARIO DUPLICADO
        // -----------------------------------------------------

        bool usuarioExiste =
            usuarios.Any(
                u =>
                    u.Id != empleadoReal.Id &&
                    u.NombreUsuario.Equals(
                        nombreUsuario,
                        StringComparison.OrdinalIgnoreCase
                    )
            );


        if (usuarioExiste)
        {
            throw new InvalidOperationException(
                "Ya existe otro empleado con ese nombre de usuario."
            );
        }


        // -----------------------------------------------------
        // ACTUALIZAR DATOS
        // -----------------------------------------------------

        empleadoReal.Nombre =
            nombre;

        empleadoReal.Telefono =
            telefono;

        empleadoReal.NombreUsuario =
            nombreUsuario;

        empleadoReal.Password =
            password;

        empleadoReal.Rol =
            "Vendedor";

        empleadoReal.Activo =
            activo;


        // -----------------------------------------------------
        // GUARDAR
        // -----------------------------------------------------

        await _repoUsuarios.UpdateAsync(
            empleadoReal
        );

        return empleadoReal;
    }


    // =========================================================
    // CAMBIAR ESTADO DEL EMPLEADO
    // =========================================================

    public async Task<Usuario> CambiarEstadoAsync(
        int usuarioId,
        bool activo)
    {
        Usuario empleado =
            await ObtenerEmpleadoRealAsync(
                usuarioId
            );


        empleado.Activo =
            activo;


        await _repoUsuarios.UpdateAsync(
            empleado
        );


        return empleado;
    }


    // =========================================================
    // DESACTIVAR EMPLEADO
    // =========================================================

    public async Task<Usuario> DesactivarEmpleadoAsync(
        int usuarioId)
    {
        Usuario empleado =
            await ObtenerEmpleadoRealAsync(
                usuarioId
            );


        if (!empleado.Activo)
        {
            throw new InvalidOperationException(
                "El empleado ya se encuentra desactivado."
            );
        }


        empleado.Activo =
            false;


        await _repoUsuarios.UpdateAsync(
            empleado
        );


        return empleado;
    }


    // =========================================================
    // OBTENER EMPLEADO REAL
    // =========================================================

    private async Task<Usuario> ObtenerEmpleadoRealAsync(
        int usuarioId)
    {
        if (usuarioId <= 0)
        {
            throw new InvalidOperationException(
                "El identificador del empleado no es válido."
            );
        }


        await _repoUsuarios.ReloadAsync();


        Usuario? empleado =
            (await _repoUsuarios.GetAllAsync())
            .FirstOrDefault(
                u => u.Id == usuarioId
            );


        if (empleado == null)
        {
            throw new InvalidOperationException(
                "El empleado ya no existe."
            );
        }


        return empleado;
    }


    // =========================================================
    // VALIDAR TELÉFONO
    // =========================================================

    private static void ValidarTelefono(
        string telefono)
    {
        // El teléfono es opcional.
        if (string.IsNullOrWhiteSpace(telefono))
        {
            return;
        }


        if (telefono.Length != 10 ||
            !telefono.All(char.IsDigit))
        {
            throw new InvalidOperationException(
                "El teléfono debe contener exactamente 10 números."
            );
        }
    }
}