import {createOwnerAccessHandler,ownerConfig} from './handler.ts';
Deno.serve(createOwnerAccessHandler(ownerConfig()));
