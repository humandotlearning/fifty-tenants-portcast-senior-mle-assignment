# Reflection

## Uncertain decision

- **Separate VPCs:** I am unsure whether each customer needs a separate network. Customer network-separation requirements would change this choice.
- **Regions:** I am unsure whether to use multiple regions, or how many. Required recovery time, acceptable outage risk, and added regional cost would decide this.
- **Backups:** I have not chosen detailed backup and restore arrangements. Acceptable data loss, retention requirements, and restore-test results would guide this choice.
- **S3 Glacier:** I am unsure about the required retention periods and retrieval times.
- I left these details out of the diagram pending requirements. The design notes mention backups and restore tests, but the diagram does not specify detailed backup or archive policies.
- Answer accuracy is unmeasured. Timing, shipment coverage, and spend do not establish correctness. Check answers against verified facts before claiming accuracy.
- Agent eval was not discussed in the architecture proposal.


## AI error

- On an AI call while discussing the data analysis charts, it gave wrong context to the wrong chat, thus making suboptimal results so I had to redo that part.
- The AI used about 2,000 users for the fifty-customer design at start and later corrected it to 5,267 users by checking the actual customer list and data analysis on the data.


