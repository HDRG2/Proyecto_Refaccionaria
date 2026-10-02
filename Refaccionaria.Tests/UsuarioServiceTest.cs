using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

using Xunit;

namespace Refaccionaria.Tests;

public class UsuarioServiceTests
{
    [Fact]
    public async Task Empleado_DebePoderDesactivarseYReactivarse()
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

        string rutaUsuarios =
            Path.Combine(
                carpetaData,
                "usuarios.json"
            );

        await File.WriteAllTextAsync(
            rutaUsuarios,
            "[]"
        );

        try
        {
            // =============================================
            // CREAR REPOSITORIO Y SERVICIO
            // =============================================

            JsonRepository<Usuario> repoUsuarios =
                new(rutaUsuarios);

            UsuarioService usuarioService =
                new(repoUsuarios);


            // =============================================
            // CREAR EMPLEADO ACTIVO
            // =============================================

            Usuario pedro =
                await usuarioService.CrearEmpleadoAsync(
                    "Pedro Lopez",
                    "8154695245",
                    "P201",
                    "12345",
                    true
                );

            Assert.True(pedro.Activo);


            // =============================================
            // DESACTIVAR EMPLEADO
            // =============================================

            Usuario desactivado =
                await usuarioService.DesactivarEmpleadoAsync(
                    pedro.Id
                );

            Assert.False(desactivado.Activo);


            // =============================================
            // COMPROBAR EN EL JSON
            // =============================================

            await repoUsuarios.ReloadAsync();

            Usuario pedroDesactivado =
                (await repoUsuarios.GetAllAsync())
                .Single(u => u.Id == pedro.Id);

            Assert.False(
                pedroDesactivado.Activo
            );


            // =============================================
            // REACTIVAR EMPLEADO
            // =============================================

            Usuario reactivado =
                await usuarioService.CambiarEstadoAsync(
                    pedro.Id,
                    true
                );

            Assert.True(reactivado.Activo);


            // =============================================
            // COMPROBAR OTRA VEZ EN EL JSON
            // =============================================

            await repoUsuarios.ReloadAsync();

            Usuario pedroReactivado =
                (await repoUsuarios.GetAllAsync())
                .Single(u => u.Id == pedro.Id);

            Assert.True(
                pedroReactivado.Activo
            );


            // =============================================
            // EL EMPLEADO NO DEBE HABER SIDO ELIMINADO
            // =============================================

            var usuarios =
                (await repoUsuarios.GetAllAsync())
                .ToList();

            Assert.Single(usuarios);

            Assert.Equal(
                "P201",
                usuarios[0].NombreUsuario
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
    public async Task EditarEmpleado_NoDebePermitirUsuarioDeOtroEmpleado()
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

        string rutaUsuarios =
            Path.Combine(
                carpetaData,
                "usuarios.json"
            );

        await File.WriteAllTextAsync(
            rutaUsuarios,
            "[]"
        );


        try
        {
            // =================================================
            // 2. CREAR REPOSITORIO Y SERVICIO TEMPORALES
            // =================================================

            JsonRepository<Usuario> repoUsuarios =
                new(rutaUsuarios);

            UsuarioService usuarioService =
                new(repoUsuarios);


            // =================================================
            // 3. CREAR DOS EMPLEADOS
            // =================================================

            Usuario jose =
                await usuarioService.CrearEmpleadoAsync(
                    "Jose Remires",
                    "8111111111",
                    "Jose2001",
                    "12345",
                    true
                );

            Usuario pedro =
                await usuarioService.CrearEmpleadoAsync(
                    "Pedro Lopez",
                    "8222222222",
                    "P201",
                    "67890",
                    true
                );


            // =================================================
            // 4. INTENTAR PONERLE A PEDRO EL USUARIO DE JOSE
            // =================================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await usuarioService.EditarEmpleadoAsync(
                            pedro,
                            "Pedro Lopez",
                            "8222222222",
                            "jose2001",
                            "67890",
                            true
                        )
                );


            // =================================================
            // 5. COMPROBAR EL MENSAJE
            // =================================================

            Assert.Equal(
                "Ya existe otro empleado con ese nombre de usuario.",
                error.Message
            );


            // =================================================
            // 6. RECARGAR EL JSON TEMPORAL
            // =================================================

            await repoUsuarios.ReloadAsync();

            var usuarios =
                (await repoUsuarios.GetAllAsync())
                .ToList();


            // =================================================
            // 7. DEBEN SEGUIR EXISTIENDO SOLO LOS DOS
            // =================================================

            Assert.Equal(
                2,
                usuarios.Count
            );


            // =================================================
            // 8. COMPROBAR QUE JOSE CONSERVA SU USUARIO
            // =================================================

            Usuario joseGuardado =
                usuarios.Single(
                    u => u.Id == jose.Id
                );

            Assert.Equal(
                "Jose2001",
                joseGuardado.NombreUsuario
            );


            // =================================================
            // 9. COMPROBAR QUE PEDRO SIGUE TENIENDO P201
            // =================================================

            Usuario pedroGuardado =
                usuarios.Single(
                    u => u.Id == pedro.Id
                );

            Assert.Equal(
                "P201",
                pedroGuardado.NombreUsuario
            );
        }
        finally
        {
            // =================================================
            // 10. ELIMINAR DATOS TEMPORALES
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

    public async Task CrearEmpleado_NoDebePermitirTelefonoInvalido()
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

        string rutaUsuarios =
            Path.Combine(
                carpetaData,
                "usuarios.json"
            );

        await File.WriteAllTextAsync(
            rutaUsuarios,
            "[]"
        );


        try
        {
            // =================================================
            // 2. CREAR REPOSITORIO Y SERVICIO TEMPORALES
            // =================================================

            JsonRepository<Usuario> repoUsuarios =
                new(rutaUsuarios);

            UsuarioService usuarioService =
                new(repoUsuarios);


            // =================================================
            // 3. INTENTAR CREAR EMPLEADO CON TELÉFONO INVÁLIDO
            // =================================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await usuarioService.CrearEmpleadoAsync(
                            "Juan Perez",
                            "12345",
                            "JP200",
                            "12345",
                            true
                        )
                );


            // =================================================
            // 4. COMPROBAR EL MENSAJE
            // =================================================

            Assert.Equal(
                "El teléfono debe contener exactamente 10 números.",
                error.Message
            );


            // =================================================
            // 5. COMPROBAR QUE NO SE GUARDÓ EL EMPLEADO
            // =================================================

            await repoUsuarios.ReloadAsync();

            var usuarios =
                (await repoUsuarios.GetAllAsync())
                .ToList();

            Assert.Empty(usuarios);
        }
        finally
        {
            // =================================================
            // 6. ELIMINAR ARCHIVOS TEMPORALES
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
    public async Task CrearEmpleado_NoDebePermitirUsuarioDuplicado()
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

        Directory.CreateDirectory(
            carpetaTemporal
        );


        string carpetaData =
            Path.Combine(
                carpetaTemporal,
                "Data"
            );

        Directory.CreateDirectory(
            carpetaData
        );


        string rutaUsuarios =
            Path.Combine(
                carpetaData,
                "usuarios.json"
            );


        // =================================================
        // 2. CREAR JSON VACÍO
        // =================================================

        await File.WriteAllTextAsync(
            rutaUsuarios,
            "[]"
        );


        try
        {
            // =============================================
            // 3. CREAR REPOSITORIO TEMPORAL
            // =============================================

            JsonRepository<Usuario> repoUsuarios =
                new(
                    rutaUsuarios
                );


            UsuarioService usuarioService =
                new(
                    repoUsuarios
                );


            // =============================================
            // 4. CREAR PRIMER EMPLEADO
            // =============================================

            Usuario pedro =
                await usuarioService.CrearEmpleadoAsync(
                    "Pedro Lopez",
                    "8154695245",
                    "P201",
                    "12345",
                    true
                );


            // =============================================
            // 5. COMPROBAR QUE SE CREÓ
            // =============================================

            Assert.True(
                pedro.Id > 0
            );

            Assert.Equal(
                "P201",
                pedro.NombreUsuario
            );


            // =============================================
            // 6. INTENTAR CREAR USUARIO DUPLICADO
            // =============================================

            InvalidOperationException error =
                await Assert.ThrowsAsync<InvalidOperationException>(
                    async () =>
                        await usuarioService.CrearEmpleadoAsync(
                            "Juan Perez",
                            "8112345678",
                            "p201",
                            "67890",
                            true
                        )
                );


            // =============================================
            // 7. COMPROBAR MENSAJE
            // =============================================

            Assert.Equal(
                "Ya existe un empleado con ese nombre de usuario.",
                error.Message
            );


            // =============================================
            // 8. RECARGAR DESDE EL JSON TEMPORAL
            // =============================================

            await repoUsuarios.ReloadAsync();

            var usuarios =
                (await repoUsuarios.GetAllAsync())
                .ToList();


            // =============================================
            // 9. DEBE SEGUIR EXISTIENDO SOLO UNO
            // =============================================

            Assert.Single(
                usuarios
            );


            Assert.Equal(
                "P201",
                usuarios[0].NombreUsuario
            );
        }
        finally
        {
            // =============================================
            // 10. BORRAR TODOS LOS DATOS DE LA PRUEBA
            // =============================================

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