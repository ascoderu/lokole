using Microsoft.Azure.ServiceBus;
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Net.Http;
using System.Net.Http.Headers;

namespace queueconnector
{
    public class Program
    {
        private static readonly Lazy<QueueClient> QueueClient = new Lazy<QueueClient>(() =>
            new QueueClient(new ServiceBusConnectionStringBuilder
            {
                Endpoint = Env.Namespace,
                EntityPath = Env.Queue,
                SasKey = Env.SasKey,
                SasKeyName = Env.SasName
            }
        ));

        private static readonly Lazy<HttpClient> HttpClient = new Lazy<HttpClient>(() =>
            new HttpClient
            {
                BaseAddress = new Uri(Env.Url)
            }
        );

        public static void Main(string[] args)
        {
            MainAsync().GetAwaiter().GetResult();
        }

        private static async Task MainAsync()
        {
            QueueClient.Value.RegisterMessageHandler(HandleMessage, new MessageHandlerOptions(HandleError)
            {
                MaxConcurrentCalls = 1,
                AutoComplete = false
            });

            await Console.Out.WriteLineAsync($"Queue connector {Env.Queue}: Starting listening");

            try
            {
                await Task.Delay(Timeout.Infinite);
            }
            finally
            {
                await QueueClient.Value.CloseAsync();
                await Console.Out.WriteLineAsync($"Queue connector {Env.Queue}: Shutting down");
            }
        }

        async static private Task HandleMessage(Message message, CancellationToken token)
        {
            await Console.Out.WriteLineAsync($"Message {message.MessageId}: Received");

            HttpResponseMessage response;
            using (var request = new ByteArrayContent(message.Body))
            {
                request.Headers.ContentType = new MediaTypeHeaderValue("application/json");
                response = await HttpClient.Value.PostAsync(string.Empty, request);
            }

            if (response.IsSuccessStatusCode)
            {
                await QueueClient.Value.CompleteAsync(message.SystemProperties.LockToken);
                await Console.Out.WriteLineAsync($"Message {message.MessageId}: Done");
            }
            else
            {
                var error = response.Content.ReadAsStringAsync();
                await Console.Error.WriteLineAsync($"Message {message.MessageId}: Error {error}");
            }
        }

        async static private Task HandleError(ExceptionReceivedEventArgs args)
        {
            var exception = args.Exception;
            var context = args.ExceptionReceivedContext;

            await Console.Error.WriteLineAsync(
                $"Message handler for {Env.Queue} encountered an exception: {exception}. " +
                $"Endpoint={context.Endpoint} EntityPath={context.EntityPath} Action={context.Action}");
        }
    }

    internal class Env
    {
        public static readonly string Namespace = Environment.GetEnvironmentVariable("LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE");
        public static readonly string SasName = Environment.GetEnvironmentVariable("LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME");
        public static readonly string SasKey = Environment.GetEnvironmentVariable("LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY");

        public static readonly string Queue = Environment.GetEnvironmentVariable("LOKOLE_SOURCE_QUEUE");
        public static readonly string Url = Environment.GetEnvironmentVariable("LOKOLE_POST_URL");
    }
}
