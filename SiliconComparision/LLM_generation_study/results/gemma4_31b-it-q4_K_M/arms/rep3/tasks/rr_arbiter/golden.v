module rr_arbiter (
    input            clk,
    input            reset,
    input      [3:0] req,
    input            advance,   // the grant is taken this cycle: move the priority past it
    output reg [3:0] gnt
);
    reg  [1:0] last;
    wire [1:0] gnt_idx = gnt[3] ? 2'd3 : gnt[2] ? 2'd2 : gnt[1] ? 2'd1 : 2'd0;

    always @(*) begin
        gnt = 4'b0000;
        case (last)
            2'd0: if      (req[1]) gnt = 4'b0010;
                  else if (req[2]) gnt = 4'b0100;
                  else if (req[3]) gnt = 4'b1000;
                  else if (req[0]) gnt = 4'b0001;
            2'd1: if      (req[2]) gnt = 4'b0100;
                  else if (req[3]) gnt = 4'b1000;
                  else if (req[0]) gnt = 4'b0001;
                  else if (req[1]) gnt = 4'b0010;
            2'd2: if      (req[3]) gnt = 4'b1000;
                  else if (req[0]) gnt = 4'b0001;
                  else if (req[1]) gnt = 4'b0010;
                  else if (req[2]) gnt = 4'b0100;
            default:
                  if      (req[0]) gnt = 4'b0001;
                  else if (req[1]) gnt = 4'b0010;
                  else if (req[2]) gnt = 4'b0100;
                  else if (req[3]) gnt = 4'b1000;
        endcase
    end

    always @(posedge clk) begin
        if (reset)
            last <= 2'd3;
        else if (advance && (gnt != 4'b0000))
            last <= gnt_idx;
    end
endmodule
