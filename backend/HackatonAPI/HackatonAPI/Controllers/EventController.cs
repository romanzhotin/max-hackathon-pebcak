using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using HtmlAgilityPack;
using System.Xml;

namespace HackatonAPI.Controllers
{
    [ApiController]
    [Route("Events")]
    public class EventController : ControllerBase
    {
        private readonly string[] allowedCities =
        {
            "msk", "spb", "nn", "kzn", "hbr",
        };

        [HttpGet("{city}")]
        public async Task<ActionResult<List<JsonElement>>> GetEvents(string city)
        {
            if (!allowedCities.Contains(city))
            {
                return BadRequest(new ProblemDetails
                {
                    Status = StatusCodes.Status400BadRequest,
                    Title = "Unknown city",
                    Detail = "The city is not in the list of allowed cities"
                });
            }
            var url = $"https://{city}.kassir.ru";

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");

            var html = await client.GetStringAsync(url);

            var doc = new HtmlDocument();
            doc.LoadHtml(html);

            var scriptNodes = doc.DocumentNode.SelectNodes(
                "//script[@type='application/ld+json']");

            if (scriptNodes == null)
            {
                return BadRequest(new ProblemDetails
                {
                    Status = StatusCodes.Status400BadRequest,
                    Title = "Tag <script type=\"application/ld+json> does not exist\""
                });
            }
            else if (scriptNodes.Count == 1)
            {
                string jsonContext = scriptNodes[0].InnerHtml.Trim();
                if (string.IsNullOrWhiteSpace(jsonContext))
                {
                    return BadRequest(new ProblemDetails
                    {
                        Status = StatusCodes.Status400BadRequest,
                        Title = "JSON empty",
                    });
                }

                // here serializing only events

                var result = new List<JsonElement>();

                using var jsonDoc = JsonDocument.Parse(jsonContext, new JsonDocumentOptions
                {
                    CommentHandling = JsonCommentHandling.Skip,
                    AllowTrailingCommas = true
                });

                var root = jsonDoc.RootElement;

                JsonElement graph;
                bool hasGraph = root.TryGetProperty("@graph", out graph) && graph.ValueKind == JsonValueKind.Array;

                if (hasGraph)
                {
                    foreach (var item in graph.EnumerateArray())
                    {
                        if (IsEvent(item))
                        {
                            result.Add(item.Clone());
                        }
                    }
                }
                else
                {
                    if (root.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var item in root.EnumerateArray())
                        {
                            if (IsEvent(item))
                            {
                                result.Add(item.Clone());
                            }
                        }
                    }
                    else if (IsEvent(root))
                    {
                        result.Add(root.Clone());
                    }
                }
                return Ok(result);
            }

            return BadRequest(new ProblemDetails
            {
                Status = StatusCodes.Status400BadRequest,
                Title = "More than 2 elements",
            });
        }

        // check if the JsonElement is event
        private static bool IsEvent(JsonElement element)
        {
            if (element.ValueKind != JsonValueKind.Object)
            {
                return false;
            }

            foreach (var propName in new[] { "@type", "type" })
            {
                if (!element.TryGetProperty(propName, out var typeProp))
                    continue;

                switch (typeProp.ValueKind)
                {
                    case JsonValueKind.String:
                        if (string.Equals(typeProp.GetString(), "Event", StringComparison.OrdinalIgnoreCase))
                        {
                            return true;
                        }
                        break;

                    case JsonValueKind.Array:
                        foreach (var t in typeProp.EnumerateArray())
                        {
                            if (t.ValueKind == JsonValueKind.String && string.Equals(t.GetString(), "Event", StringComparison.OrdinalIgnoreCase))
                            {
                                return true;
                            }
                        }
                        break;
                }
            }
            return false;
        }
    }
}
