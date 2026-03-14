/**
 * MSW Node server instance.
 *
 * Import this in `src/test/setup.ts` for global lifecycle wiring.
 * Individual tests can also import it to call `server.use(overrideHandler)`.
 */

import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
