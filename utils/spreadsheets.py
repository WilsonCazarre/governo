class Spreadsheet:
    def __init__(self, sheet_id: str, api_service, query_range: str):
        self.sheet_id = sheet_id
        self.api_service = api_service
        self.query_range = query_range

    def get_rows(self):
        spreadsheet = (
            self.api_service.values()
            .get(
                spreadsheetId=self.sheet_id,
                range=self.query_range,
            )
            .execute()
        )
        raw_values = spreadsheet.get("values", [])
        if len(raw_values) == 0:
            return raw_values

        keys = raw_values.pop(0)
        return [dict(zip(keys, row)) for row in raw_values]

    def add_rows(self, *rows, input_option="RAW"):
        self.api_service.values().append(
            spreadsheetId=self.sheet_id,
            range=self.query_range,
            valueInputOption=input_option,
            body={"values": rows},
        ).execute()
