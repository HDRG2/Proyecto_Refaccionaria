using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace Refaccionaria.Frontend.Services;

public sealed class ServidorIAService
{
    private Process? procesoServidor;

    private bool cierreSolicitado = false;

    private readonly object bloqueoProceso = new();

    private static readonly HttpClient cliente = new()
    {
        Timeout = TimeSpan.FromSeconds(3)
    };


    public async Task IniciarAsync()
    {
        lock (bloqueoProceso)
        {
            if (cierreSolicitado)
                return;
        }

        // Evitar iniciar otro servidor si ya está disponible.
        if (await ServidorDisponibleAsync())
            return;

        string? ejecutable = BuscarEjecutableServidor();
        string? carpetaProyecto = BuscarCarpetaProyecto();

        ProcessStartInfo configuracion;

        if (ejecutable != null)
        {
            // Utilizar el servidor empaquetado.
            configuracion = new ProcessStartInfo
            {
                FileName = ejecutable,
                WorkingDirectory = Path.GetDirectoryName(ejecutable)!,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            Debug.WriteLine("IA: Utilizando ServidorIA.exe.");
        }
        else
        {
            // Respaldo para el entorno de desarrollo.
            if (carpetaProyecto == null)
            {
                Debug.WriteLine(
                    "IA: No se encontró el servidor ni el proyecto."
                );
                return;
            }

            string python = Path.Combine(
                carpetaProyecto,
                ".venv-autogen",
                "Scripts",
                "python.exe"
            );

            if (!File.Exists(python))
            {
                Debug.WriteLine(
                    "IA: No se encontró Python ni ServidorIA.exe."
                );
                return;
            }

            configuracion = new ProcessStartInfo
            {
                FileName = python,
                Arguments =
                    "-m uvicorn AgenteIA.servidor:app " +
                    "--host 127.0.0.1 --port 8000",
                WorkingDirectory = carpetaProyecto,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            Debug.WriteLine("IA: Utilizando Python de desarrollo.");
        }

        try
        {
            Process? procesoIniciado;

            lock (bloqueoProceso)
            {
                if (cierreSolicitado)
                    return;

                procesoServidor = Process.Start(configuracion);
                procesoIniciado = procesoServidor;
            }

            if (procesoIniciado == null)
            {
                Debug.WriteLine(
                    "IA: No se pudo iniciar el servidor."
                );
                return;
            }

            // Esperar hasta aproximadamente 15 segundos.
            for (int intento = 0; intento < 30; intento++)
            {
                lock (bloqueoProceso)
                {
                    if (cierreSolicitado)
                        return;

                    if (procesoIniciado.HasExited)
                    {
                        Debug.WriteLine(
                            "IA: El servidor terminó durante el arranque."
                        );
                        return;
                    }
                }

                if (await ServidorDisponibleAsync())
                {
                    lock (bloqueoProceso)
                    {
                        if (cierreSolicitado)
                            return;
                    }

                    Debug.WriteLine(
                        "IA: Servidor iniciado correctamente."
                    );
                    return;
                }

                await Task.Delay(500);
            }

            Debug.WriteLine(
                "IA: El servidor no respondió a tiempo."
            );
        }
        catch (Exception ex)
        {
            Debug.WriteLine(
                $"IA: Error al iniciar el servidor: {ex.Message}"
            );
        }
    }


    private static async Task<bool> ServidorDisponibleAsync()
    {
        try
        {
            using var respuesta = await cliente.GetAsync(
                "http://127.0.0.1:8000/openapi.json"
            );

            return respuesta.IsSuccessStatusCode;
        }
        catch (HttpRequestException)
        {
            return false;
        }
        catch (TaskCanceledException)
        {
            return false;
        }
    }

    private static string? BuscarEjecutableServidor()
    {
        DirectoryInfo? carpeta = new(
            AppContext.BaseDirectory
        );

        while (carpeta != null)
        {
            // Para una instalación: junto al ejecutable de WinUI.
            string rutaInstalada = Path.Combine(
                carpeta.FullName,
                "ServidorIA",
                "ServidorIA.exe"
            );

            if (File.Exists(rutaInstalada))
                return rutaInstalada;

            // Para desarrollo: salida de PyInstaller.
            string rutaDesarrollo = Path.Combine(
                carpeta.FullName,
                "dist",
                "ServidorIA",
                "ServidorIA.exe"
            );

            if (File.Exists(rutaDesarrollo))
                return rutaDesarrollo;

            carpeta = carpeta.Parent;
        }

        return null;
    }

    private static string? BuscarCarpetaProyecto()
    {
        DirectoryInfo? carpeta = new(
            AppContext.BaseDirectory
        );

        while (carpeta != null)
        {
            string servidor = Path.Combine(
                carpeta.FullName,
                "AgenteIA",
                "servidor.py"
            );

            if (File.Exists(servidor))
                return carpeta.FullName;

            carpeta = carpeta.Parent;
        }

        return null;
    }

    public void Detener()
    {
        lock (bloqueoProceso)
        {
            cierreSolicitado = true;

            if (procesoServidor == null)
                return;

            try
            {
                if (!procesoServidor.HasExited)
                {
                    procesoServidor.Kill(
                        entireProcessTree: true
                    );

                    System.Diagnostics.Debug.WriteLine(
                        "IA: Servidor FastAPI detenido."
                    );
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine(
                    $"IA: Error al detener FastAPI: {ex.Message}"
                );
            }
            finally
            {
                procesoServidor.Dispose();
                procesoServidor = null;
            }
        }

    }

}
