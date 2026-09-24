using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using HtmlAgilityPack;

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

        private readonly Dictionary<string, string> eventRoutes = new()
        {
            { "default", "" },
            { "koncert", "bilety-na-koncert" },
            { "teatr", "bilety-v-teatr" },
            { "shou", "bilety-na-shou" },
            { "kino", "bilety-v-kino" },
            { "children", "detskaya-afisha" },
            { "festivals", "bilety-na-festival" },
            { "excursions", "bilety-na-ekskursii" },
            { "sport", "bilety-na-sportivnye-meropriyatiya" },
            { "education", "obrazovanie-i-kursy" },
        };

        [HttpGet("{city}/{eventType}")]
        public async Task<ActionResult<List<JsonElement>>> GetEvents(
            string city,
            string eventType,
            [FromQuery] int? minPrice,
            [FromQuery] int? maxPrice,
            [FromQuery] DateTimeOffset? maxDate
            )
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

            if (!eventRoutes.ContainsKey(eventType))
            {
                return BadRequest(new ProblemDetails
                {
                    Status = StatusCodes.Status400BadRequest,
                    Title = "Unknown event type",
                    Detail = "The event type is unknown"
                });
            }
            var url = $"https://{city}.kassir.ru/{eventRoutes[eventType]}";

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

                var events = new List<JsonElement>();

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
                            events.Add(item.Clone());
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
                                events.Add(item.Clone());
                            }
                        }
                    }
                    else if (IsEvent(root))
                    {
                        events.Add(root.Clone());
                    }
                }

                // if not given filter params - return all
                if (minPrice is null && maxPrice is null && maxDate is null)
                {
                    return Ok(events);
                }

                try
                {
                    var result = FilterEvents(events, minPrice, maxPrice, maxDate);

                    return Ok(result);
                }
                catch (Exception ex)
                {
                    return BadRequest(new ProblemDetails
                    {
                        Status = StatusCodes.Status400BadRequest,
                        Title = ex.Message
                    });
                }
                
            }

            return BadRequest(new ProblemDetails
            {
                Status = StatusCodes.Status400BadRequest,
                Title = "More than 2 elements",
            });
        }

        // filter events
        private static List<JsonElement> 
            FilterEvents(List<JsonElement> events, int? minPrice, int? maxPrice, DateTimeOffset? maxDate)
        {
            List<JsonElement> result = new List<JsonElement>();
            foreach (var e in events)
            {
                bool acceptPrice = false, acceptDate = false;

                // price
                var offerInfo = e.GetProperty("offers");

                if (offerInfo.ValueKind != JsonValueKind.Object)
                {
                    throw new Exception("Event has no property \"offers\"");
                }

                var price = offerInfo.GetProperty("price").GetInt32();

                if (price >= (minPrice ?? 0) && price <= (maxPrice ?? int.MaxValue))
                {
                    acceptPrice = true;
                }

                // date
                var startDate = e.GetProperty("startDate").GetDateTimeOffset();

                if (startDate <= (maxDate ?? DateTimeOffset.MaxValue))
                {
                    acceptDate = true;
                }

                if (acceptPrice && acceptDate)
                {
                    result.Add(e.Clone());
                }
            }

            return result;
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
