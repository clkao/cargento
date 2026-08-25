# Session interaction origin breadboard

This breadboard compares registered tmux delivery with a transport-neutral mailbox contract.
It does not add a product feature.

The exercise used commit `2357af3` and tmux 3.7b. It did not read a transcript or a harness store.
It did not use an existing terminal session.

## Inspect the exercise

Run this command from the repository root:

```bash
python3 docs/plans/session-interaction-origin-breadboard.py
```

The script starts a new isolated tmux server. It starts two candidate sessions on that server.
Only the first candidate gets a registration. A `finally` block stops the isolated server.

The committed result is
[`session-interaction-origin-breadboard-results.json`](session-interaction-origin-breadboard-results.json).
The script exits with an error if an isolation, integrity, or outcome assertion fails.

## Registered tmux mechanism

The spike uses a server-owned registration with these fields:

- An opaque channel ID identifies the registration to the browser.
- A pane ID identifies the receiver inside the transport adapter.
- A tmux server PID prevents delivery after socket reuse.
- An expiry time limits the registration lifetime.

The browser request contains only `channel_id` and `text`. The router rejects all extra fields.
Thus, the browser cannot supply a pane ID, a socket name, or a shell action.

The adapter passes a JSON envelope to `tmux load-buffer` through standard input. It then runs
`tmux paste-buffer` against the registered pane ID. It never builds a shell command from the text.

The receiver sends a receipt after it reads the envelope. A successful tmux command does not mean
`acknowledged`. Without an application receipt, the result is `unknown`.

## Observed results

| Case | Result | Byte evidence |
|---|---|---|
| Registered target | `acknowledged` | The receiver recorded the exact text. |
| Unregistered target | `refused: unregistered-origin` | The second candidate recorded zero bytes. |
| Session policy rejects | `rejected` | The registered receiver recorded the exact text and rejected it. |
| Receipt path absent | `unknown: receipt-timeout` | The receiver recorded the text, but no receipt existed. |
| Browser supplies a locator | `refused: malformed-request` | The registered receiver recorded zero new messages. |
| Shell metacharacters in text | `acknowledged` | The receiver recorded exact text. No shell marker file existed. |
| Registration expired | `refused: stale-registration` | The registered receiver recorded zero new messages. |
| Registered pane closed | `unknown: transport-disconnected` | The receiver recorded zero new messages. |

The tmux spike proves exact targeting only when the registered pane runs the receiver protocol.
It does not prove that pasting into an arbitrary foreground program is safe.

A shell can execute pasted metacharacters after an Enter key. An editor can interpret pasted bytes
as commands. A harness TUI can change its input mode before delivery.

Therefore, a bare pane registration is not a sufficient application boundary. A tmux adapter needs
a receiver protocol and an application receipt. With that receiver, tmux is only the byte transport.

## Transport-neutral registered mailbox contract

The existing ask lane supplies the useful primitives. It uses bounded long polls, one-slot outcomes,
explicit expiry, and a shutdown decline. The candidate contract reverses the direction. It does not
give the browser a transport target.

### Registration

A session starts a local client and registers one interaction origin. The candidate record has these
fields:

- `channel_id`: an opaque ID that the page can address.
- `client_auth`: session-only authentication material. Review must select its form.
- `session_key`: the Cargento row that the origin claims.
- `generation`: the server-run and client-run generation.
- `expires_at`: the registration deadline.

The page receives the `channel_id` and visible session attribution. It does not receive `client_auth`,
the poll address, a tmux locator, or a shell action.

### Operator request

The page sends this bounded shape after an explicit operator action:

```json
{"channel_id":"opaque","text":"bounded plain text"}
```

The server rejects unknown, expired, and malformed requests before it creates a mailbox entry.
Each registration has at most one outstanding entry. A second request gets a visible refusal.

### Session poll and receipt

The client makes a bounded long poll with its `channel_id`, `client_auth`, and `generation`.
The server returns one envelope with a new `message_id` and the registered text.

The client sends one receipt for that `message_id`. The receipt state is `acknowledged` or `rejected`.
The receipt carries no free-form text that can enter the page as operator-authored content.

The server reports these final outcomes:

- `acknowledged`: the registered client explicitly accepted the message.
- `rejected`: the registered client explicitly rejected the message.
- `refused`: the server sent zero bytes because the request was invalid, stale, or over budget.
- `unknown`: the server cannot prove the result because the receipt path failed or expired.

The page can show `queued` before a receipt. It must not show `sent`, `delivered`, or `acknowledged`
before the matching receipt arrives.

The server must not retry an `unknown` message automatically. A retry needs a stable message ID,
client deduplication, and a second explicit operator action.

## Mechanism comparison

| Property | Registered tmux adapter | Registered mailbox |
|---|---|---|
| Browser authority | Opaque channel ID only | Opaque channel ID only |
| Hidden target | Server socket, PID, and pane ID | Client authentication and generation |
| Session participation | A receiver must run in the pane | A client must register and poll |
| Exact text | Observed through the receiver protocol | The contract preserves the envelope text |
| Application receipt | Requires a receiver shim | Required by the contract |
| Missing receipt | `unknown` | `unknown` |
| Stale origin | Expiry plus tmux server PID | Expiry plus server and client generations |
| Shell boundary | Unsafe without a receiver protocol | The client receives structured data, not shell input |
| Platform cost | Requires tmux and a stable pane | Requires loopback HTTP and a small client |
| Foreground-mode risk | The pane can change programs or modes | The registered client owns message handling |

The mailbox is the stronger development direction. It makes application consent part of the
transport contract. It also uses the long-poll shape that Cargento already operates.

The tmux result remains useful as a falsifier. It proves that server-owned target resolution and
literal delivery work. It also proves that transport success alone cannot support a success label.

## Choices that still matter

The captain must accept the security and consent boundary before development starts. These choices
remain open:

1. How does a client prove that it owns the claimed `session_key`?
2. Is the payload bounded plain text, a fixed action vocabulary, or session-supplied options?
3. Does registration last for one turn, one session process, or a short renewable lease?
4. What receipt timeout changes `queued` to `unknown`?
5. Can one registration hold one pending message, or a small bounded queue?
6. Does a retry reuse a message ID, and how does the client store deduplication state?
7. Is a tmux receiver adapter supported, or does development start with loopback long polling only?
8. Which same-origin and client-authentication checks protect registration, polling, and receipts?

The payload choice has the largest security effect. Plain text is more powerful than the ask lane's
index response. A fixed action vocabulary has a smaller forgery and interpretation boundary.

No development task exists until the captain accepts these choices. The breadboard recommends a
registered long-poll mailbox and rejects direct paste into an arbitrary session terminal.
