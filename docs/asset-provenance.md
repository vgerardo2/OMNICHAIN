# Source and asset provenance checklist

This inventory records known origins and remaining release work. It does not
establish permission for material whose original license is unknown.

| Material | Recorded origin | State |
| --- | --- | --- |
| Python implementation, tests, and project documentation | Created in this project for the synthetic prototype | Included under the repository's Apache 2.0 license. |
| Scenario data | Authored fictional supplier, invoice fields, recipients, and fake restricted value | Synthetic; no customer material is required. |
| UI effects and CSS references | User-provided snippets, adapted in the project | Original authors/source URLs and redistribution terms have not all been established. Review before claiming complete third-party clearance. |
| OC lettermark | Text rendered by local CSS | No downloaded logo image is needed. |
| Fonts | Browser/system fallback fonts | No bundled external font download is required. |
| Icon markers | Existing `data-lucide` markup; no icon library is bundled or fetched by the app | Review source/license if an icon package is added. |
| Photos and source-reference videos | Local design references | Excluded from the Git release; do not redistribute by default. |
| HutchDB | Source review only | No code or dependency adopted. |
| Gemma/JEV services | Optional external inference plans/adapters | Provider/model terms are separate; no live service is required by the scripted demo. |

Record source URL, author, license version, affected file/section, and any required
attribution for each reused asset. If an origin cannot be established, replace
that material with a documented original implementation before marking release
provenance complete. Do not silently declare all reference snippets Apache-licensed.
