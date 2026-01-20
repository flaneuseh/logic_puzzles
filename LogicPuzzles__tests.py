if __name__ == "__main__":
    suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
    weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time])

# %% colab={"base_uri": "https://localhost:8080/"} id="i0iWKiURMcWG" outputId="c37df34f-453d-4128-8966-e66129961c3d"

if __name__ == "__main__":
    print("Test board arrangement")
    print(" " * 7 + " ".join([str(ent) for ent in puzzle.left_right]))
    print("\n".join([str(ent) for ent in puzzle.top_bottom]))
    print(puzzle.print_grid())

# %% colab={"base_uri": "https://localhost:8080/"} id="5y0jCd1KcEO3" outputId="0c5dae69-7b4f-4467-e76e-291ebb128933"
if __name__ == "__main__":
    print("Answer Knife = Study and Knife = Scarlet")
    puzzle.answer(weapons, rooms, "Knife", "Study", "O")
    puzzle.answer(weapons, suspects, "Knife", "Scarlet", "O")

    print(puzzle.print_grid())
    print("\n")

    print("Knife: ", puzzle.find_truths(weapons, "Knife"))
    print("\n")
    print("Study: ", puzzle.find_truths(rooms, "Study"))
    print("\n")
    print("Puzzle valid? ", puzzle.is_valid())
    print("Puzzle complete? ", puzzle.is_complete())

# %% colab={"base_uri": "https://localhost:8080/"} id="HZ-W4nrF0PUo" outputId="aa2427a3-a09d-4ac3-8709-a7f90ab02187"

if __name__ == "__main__":
    print("Answer Study = White")
    puzzle.answer(rooms, suspects, "Study", "White", "O")
    print(puzzle.print_grid())
    print("Truths valid? ", puzzle._truths_valid())

# %% colab={"base_uri": "https://localhost:8080/"} id="NnIeuhBBcHWS" outputId="b6239c41-3d1f-41f6-e2b5-587f79017ed3"
if __name__ == "__main__":
    print("New puzzle")
    suspects2 = Category("suspects", ["Scarlet", "White", "Mustard"], False)
    weapons2 = Category("weapons", ["Knife", "Rope", "Candle Stick"], False)
    rooms2 = Category("rooms", ["Ball room", "Living Room", "Kitchen"], False)

    puzzle2 = Puzzle([suspects2, weapons2, rooms2])
    print(puzzle2.print_grid())

# %% colab={"base_uri": "https://localhost:8080/"} id="eTC-G36i3Tgs" outputId="be584ad7-9b58-43a0-aebd-32cb6b65097a"
if __name__ == "__main__":
    print("Answer new puzzle")
    puzzle2.answer(rooms2, suspects2, "Ball room", "White", "O")
    puzzle2.answer(rooms2, suspects2, "Living Room", "Mustard", "O")
    puzzle2.answer(rooms2, suspects2, "Kitchen", "Scarlet", "O")

    puzzle2.answer(rooms2, weapons2, "Ball room", "Knife", "O")
    puzzle2.answer(rooms2, weapons2, "Living Room", "Rope", "O")
    puzzle2.answer(rooms2, weapons2, "Kitchen", "Candle Stick", "O")

    puzzle2.answer(suspects2, weapons2, "White", "Knife", "O")
    puzzle2.answer(suspects2, weapons2, "Mustard", "Rope", "O")
    puzzle2.answer(suspects2, weapons2, "Scarlet", "Candle Stick", "O")
    print(puzzle2.print_grid())
    print("Complete? ", puzzle2.is_complete())

# Test puzzle
if __name__ == "__main__":
    suspects = Category("suspects", ["Scarlet", "White", "Mustard", "Plum"], False)
    weapons = Category("weapons", ["Knife", "Rope", "Candle Stick", "Wrench"], False)
    rooms = Category("rooms", ["Ball room", "Living Room", "Kitchen", "Study"], False)
    time = Category("Time", ["1:00", "2:00", "3:00", "4:00"], True)

    puzzle = Puzzle([suspects, weapons, rooms, time])

if __name__ == "__main__":
    print("Generate a random hint:")
    print(str_hint(generate_hint(puzzle)))

# %%
# Test is
if __name__ == "__main__":
    print("Test IS")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    # Apply when it is still blank
    print("Testing IS")
    print("New IS: Scarlet IS Knife")
    terms = [suspects, "Scarlet", weapons, "Knife"]
    applied, is_valid, complete, insights = apply_is(puzzle, terms)
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_IS},
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

    # Skip when it has already been answered O
    print("PreAnswered: Scarlet IS Knife")
    applied, is_valid, complete, insights = apply_is(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, True, True, set())
    print(puzzle.print_grid())

    # Contradiction when it has already been answered X
    print("Contradiction: Scarlet IS Rope")
    terms[3] = "Rope"
    applied, is_valid, complete, insights = apply_is(puzzle, terms)
    assert (applied, is_valid, complete, insights) == (False, False, True, set())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

# %%
# Test not
if __name__ == "__main__":
    print("Test NOT")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    terms = [suspects, "Scarlet", weapons, "Knife"]

    # Apply when it is still blank
    print("Testing NOT")
    print("New NOT: Scarlet NOT Knife")
    applied, is_valid, complete, insights = apply_not(puzzle, terms)
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_NOT},
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

    # Skip when it has already been answered O
    print("PreAnswered: Scarlet NOT Knife")
    applied, is_valid, complete, insights = apply_not(puzzle, terms)
    assert (applied, is_valid, complete, insights) == (False, True, True, set())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

    # Contradiction when it has already been answered X
    print("Set Plum is Knife")
    terms[1] = "Plum"
    apply_is(puzzle, terms)
    print("Contradiction: Plum NOT Knife")
    applied, is_valid, complete, insights = apply_not(puzzle, terms)
    assert (applied, is_valid, complete, insights) == (False, False, True, set())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

# %%
# Test find_openings
if __name__ == "__main__":
    print("Test find openings")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    print("Set up find openings")
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "Scarlet", time, "4:00"])
    apply_not(puzzle, [weapons, "Knife", time, "1:00"])
    apply_not(puzzle, [weapons, "Rope", time, "1:00"])
    print(puzzle.print_grid())

    # Find openings when there are no openings
    print("Find openings when there are no single blanks")
    applied, is_valid, complete, insights = find_openings(puzzle)
    assert (applied, is_valid, complete, insights) == (False, True, False, set())
    print(
        "(Applied, Is Valid, Complete, insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())

    # There is an opening in a column
    print("Set Mustard to 2:00")
    apply_is(puzzle, [suspects, "Mustard", time, "2:00"])
    print(puzzle.print_grid())
    print("Find an opening in a column")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.OPENING},
    )

    # There is an opening in a row
    print("Set Wrench to 3:00")
    apply_is(puzzle, [weapons, "Wrench", time, "3:00"])
    print(puzzle.print_grid())
    print("Find an opening in a row")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.OPENING},
    )

    # There is a row of all X => contradiction
    print("Set row to all X => contradiction")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "White", time, "1:00"])
    apply_not(puzzle, [suspects, "Mustard", time, "1:00"])
    apply_not(puzzle, [suspects, "Plum", time, "1:00"])
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # There is a column of all X => contradiction
    print("Set col to all X => contradiction")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "Scarlet", time, "2:00"])
    apply_not(puzzle, [suspects, "Scarlet", time, "3:00"])
    apply_not(puzzle, [suspects, "Scarlet", time, "4:00"])
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # There is a row with one O and no Xs
    print(
        "Set row to one O and no Xs => fill in blanks"
    )  # also shows a col with one O and otherwise missing blanks
    puzzle = Puzzle([suspects, weapons, rooms, time])
    puzzle.answer(suspects, time, "Scarlet", "1:00", "O")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.CROSS_OUT},
    )

    print("Set row to one O and some Xs => fill in blanks")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    puzzle.answer(suspects, time, "Scarlet", "1:00", "O")
    puzzle.answer(suspects, time, "Mustard", "1:00", "X")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.CROSS_OUT},
    )

    # There is a column with one O and missing blanks
    print("Set col to one O and some Xs => fill in missing blanks")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    puzzle.answer(suspects, time, "Scarlet", "1:00", "O")
    puzzle.answer(suspects, time, "Scarlet", "2:00", "X")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.CROSS_OUT},
    )

    # There is a row with 2 or more Os (contradiction)
    print("Set row to 2 or more Os => contradiction")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    puzzle.answer(suspects, time, "Scarlet", "1:00", "O")
    puzzle.answer(suspects, time, "White", "1:00", "O")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # There is a column with 2 or more Os (contradiction)
    print("Set col to 2 or more Os => contradiction")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    puzzle.answer(suspects, time, "Scarlet", "1:00", "O")
    puzzle.answer(suspects, time, "Scarlet", "2:00", "O")
    applied, is_valid, complete, insights = find_openings(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

# %%
# Test find_transitives
if __name__ == "__main__":
    print("Test find transitives")
    # A -> B and B -> C, so A -> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and 1:00 -> Study so Scarlet -> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_TRUE},
    )

    # A -> B and B -> C, but can't A -> C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and 1:00 -> Study but Scarlet !> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A -> B and B !> C, so A !> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and 1:00 !> Study so Scarlet !> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_FALSE},
    )

    # A -> B and B !> C, but can't A !> C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [time, "1:00", rooms, "Study"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and 1:00 !> Study but Scarlet !> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A -> B and A -> C so B -> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and Scarlet -> Study so 1:00 -> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_TRUE},
    )

    # A -> B and A -> C, but can't B -> C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    apply_not(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and Scarlet -> Study but 1:00 !> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A -> B and A !> C so B !> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and Scarlet !> Study so 1:00 !> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_FALSE},
    )

    # A -> B and A !> C, but can't B !> C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "Scarlet", rooms, "Study"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet -> 1:00 and Scarlet !> Study but 1:00 -> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A !> B and B -> C, so A !> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet !> 1:00 and 1:00 -> Study so Scarlet !> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_FALSE},
    )

    # A !> B and B -> C, , but can't reject A to C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet !> 1:00 and 1:00 -> Study, but Scarlet !> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A !> B and A -> C so B !> C
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet !> 1:00 and Scarlet -> Study so 1:00 !> Study")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_ABC_FALSE},
    )

    # A !> B and A -> C so B !> C, but can't reject B to C => contradiction
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_is(puzzle, [suspects, "Scarlet", rooms, "Study"])
    apply_is(puzzle, [time, "1:00", rooms, "Study"])
    print(puzzle.print_grid())

    print("Scarlet !> 1:00 and Scarlet -> Study, but 1:00 !> Study => contradiction")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, False, set())

    # A and B don't share any possibilities; A !> B
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    apply_not(puzzle, [suspects, "Scarlet", time, "2:00"])
    apply_not(puzzle, [weapons, "Rope", time, "3:00"])
    apply_not(puzzle, [weapons, "Rope", time, "4:00"])

    print(puzzle.print_grid())

    ## Neither Scarlet nor Rope has a O time
    print("Scarlet and Rope don't share any compatible times, so Scarlet !> Rope")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_SETS},
    )

    # Neither Scarlet nor White can be 1:00 and Ballroom can only be Scarlet or White so Ballroom is not 1:00
    apply_not(puzzle, [suspects, "White", time, "1:00"])
    apply_not(puzzle, [rooms, "Ball room", suspects, "Mustard"])
    apply_not(puzzle, [rooms, "Ball room", suspects, "Plum"])
    print(puzzle.print_grid())

    print("Ballroom and 1:00 don't share any compatible suspects, so Ballroom != 1:00")
    applied, is_valid, complete, insights = find_transitives(puzzle)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.TRANS_SETS},
    )

# %%
# Test before
if __name__ == "__main__":
    print("Testing simple BEFORE")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())
    terms = [suspects, "Scarlet", suspects, "White", time]

    # No current information; simple before
    print("Scarlet BEFORE White")
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_ONE_SPOT_NOINFO},
    )
    print(puzzle.print_grid())

    # Additional constraint on After's time
    print("White NOT 4:00 => Scarlet NOT 3:00")
    apply_not(puzzle, [suspects, "White", time, "4:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_SHIFT},
    )

    # After is set
    print("White IS 2:00 => Scarlet IS 1:00; finished hint")
    apply_is(puzzle, [suspects, "White", time, "2:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
    )

    # Already satisfied
    print("Already satisfied; no further changes")
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, True, True, set())

    # Constraints on both
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())
    print("Mustard BEFORE Plum => narrow down both")
    apply_not(puzzle, [suspects, "Mustard", time, "1:00"])
    apply_not(puzzle, [suspects, "Mustard", time, "4:00"])
    apply_not(puzzle, [suspects, "Plum", time, "1:00"])
    apply_not(puzzle, [suspects, "Plum", time, "4:00"])
    terms[1] = "Mustard"
    terms[3] = "Plum"
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_SHIFT},
    )

    # Single answer
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())
    print("Plum IS 4:00 => Mustard IS 3:00")
    apply_not(puzzle, [suspects, "Mustard", time, "1:00"])
    apply_not(puzzle, [suspects, "Mustard", time, "2:00"])
    apply_is(puzzle, [suspects, "Plum", time, "4:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
    )

    print("Candle Stick IS 3:00 and Candle Stick BEFORE Rope => Rope IS 4:00")
    apply_is(puzzle, [weapons, "Candle Stick", time, "3:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [weapons, "Candle Stick", weapons, "Rope", time]
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_UNDEFINED_SPOTS},
    )

    # Reset puzzle
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    # Constraint on Before's time.
    print("Knife before Rope; Knife NOT 1:00 => Rope NOT 2:00")
    terms = [weapons, "Knife", weapons, "Rope", time]
    apply_not(puzzle, [weapons, "Knife", time, "1:00"])
    apply_not(puzzle, [weapons, "Knife", time, "4:00"])
    apply_not(puzzle, [weapons, "Rope", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_SHIFT},
    )

    # Simple contradiction
    print("Candle is 3:00 and Wrench is 2:00; Candle BEFORE Wrench is contradictory")
    apply_is(puzzle, [weapons, "Candle Stick", time, "3:00"])
    apply_is(puzzle, [weapons, "Wrench", time, "2:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [weapons, "Candle Stick", weapons, "Wrench", time]
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # If A and B are not in the same category, A is not B
    print("White is before Ballroom, so White is not Ballroom")
    apply_not(puzzle, [suspects, "White", time, "4:00"])
    apply_not(puzzle, [rooms, "Ball room", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [suspects, "White", rooms, "Ball room", time]
    )
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_DIFF_CAT},
    )

    # Contradiction for before O
    print("Kitchen IS 4:00, so Kitchen before Study contradicts")
    apply_is(puzzle, [rooms, "Kitchen", time, "4:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [rooms, "Kitchen", rooms, "Study", time]
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # Contradiction for after 0
    print("Living room IS 1:00, so Study before Living room contradicts")
    apply_is(puzzle, [rooms, "Living Room", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [rooms, "Study", rooms, "Living Room", time]
    )
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # Numerical Before tests
    print("Test numbered BEFORE")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())
    terms_n = [suspects, "Scarlet", suspects, "White", time, 2]
    terms_1 = [weapons, "Knife", weapons, "Wrench", time, 1]

    # No current info, n
    print("Scarlet 2 BEFORE White")
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_NOINFO},
    )
    print(puzzle.print_grid())

    # No current info, 1
    print("Knife 1 BEFORE Rope")
    applied, is_valid, complete, insights = apply_before(puzzle, terms_1)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_ONE_SPOT_NOINFO},
    )
    print(puzzle.print_grid())

    # Before entity has X
    print("Scarlet NOT 1:00 and Scarlet 2 BEFORE White")
    apply_not(puzzle, [suspects, "Scarlet", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_SHIFT},
    )

    # Before entity is set
    print("Scarlet IS 2:00 and Scarlet 2 BEFORE White")
    apply_is(puzzle, [suspects, "Scarlet", time, "2:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_N_SPOTS},
    )
    print(puzzle.print_grid())

    print("Knife IS 2:00 and Knife 1 BEFORE Wrench")
    apply_is(puzzle, [weapons, "Knife", time, "2:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_1)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_ONE_SPOT},
    )
    print(puzzle.print_grid())

    # Reset puzzle
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    # After entity has X
    terms_n[1] = "Mustard"
    terms_n[3] = "Plum"
    print("Plum NOT 4:00 and Mustard 2 before Plum")
    apply_not(puzzle, [suspects, "Plum", time, "1:00"])
    apply_not(puzzle, [suspects, "Plum", time, "2:00"])
    apply_not(puzzle, [suspects, "Plum", time, "4:00"])
    apply_not(puzzle, [suspects, "Mustard", time, "4:00"])
    apply_not(puzzle, [suspects, "Mustard", time, "3:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.BEFORE_N_SPOTS_SHIFT},
    )

    # After entity is set
    print("Plum IS 3:00 and Mustard 2 before Plum")
    apply_is(puzzle, [suspects, "Plum", time, "3:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_N_SPOTS},
    )
    print(puzzle.print_grid())

    terms_1[0] = rooms
    terms_1[1] = "Living Room"
    terms_1[2] = rooms
    terms_1[3] = "Study"
    print("Study IS 3:00 and Living Room 2 before Study")
    apply_is(puzzle, [rooms, "Study", time, "3:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_1)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_BEFORE_ONE_SPOT},
    )
    print(puzzle.print_grid())

    # Both set, ok
    print("Both set; Mustard 2 before Plum")
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, True, True, set())
    print(puzzle.print_grid())

    # Before set, contradiction
    print("Knife IS 2:00; Rope NOT 4:00; Knife 2 before Rope => contradiction")
    terms_n = [weapons, "Knife", weapons, "Rope", time, 2]
    apply_is(puzzle, [weapons, "Knife", time, "2:00"])
    apply_not(puzzle, [weapons, "Rope", time, "4:00"])
    apply_not(puzzle, [weapons, "Rope", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # After set, contradiction
    print(
        "Wrench IS 3:00; Candle Stick NOT 1:00; Candle Stick 2 before Wrench => contradiction"
    )
    terms_n[1] = "Candle Stick"
    terms_n[3] = "Wrench"
    apply_is(puzzle, [weapons, "Wrench", time, "3:00"])
    apply_not(puzzle, [weapons, "Candle Stick", time, "1:00"])
    applied, is_valid, complete, insights = apply_before(puzzle, terms_n)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # Reset puzzle
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    # Both set, contradiction
    print("Kitchen IS 1:00, Study IS 2:00; Kitchen 2 before Study is contradictory")
    apply_is(puzzle, [rooms, "Kitchen", time, "1:00"])
    apply_is(puzzle, [rooms, "Study", time, "2:00"])
    applied, is_valid, complete, insights = apply_before(
        puzzle, [rooms, "Kitchen", rooms, "Study", time, 2]
    )
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

# %%
if __name__ == "__main__":
    # Test simple or
    print("Testing simple OR")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    # A and B in diff categories; no info
    terms = [suspects, "White", weapons, "Knife", rooms, "Study"]
    print(
        "Either Mrs. White OR the Knife was in the Study => Mrs. White did NOT have the Knife"
    )
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.SIMPLE_OR_DIFF_CAT},
    )

    # A and B in same category; no info
    terms = [rooms, "Kitchen", rooms, "Study", time, "1:00"]
    print("Either the Kitchen OR the Study was at 1:00 => no other room can be at 1:00")
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        False,
        {Insight.SIMPLE_OR_SAME_CAT},
    )

    # A and B in same category and a different item has the value.
    print("Knife was at 1:00 and Rope OR Wrench was at 1:00 => contradiction")
    apply_is(puzzle, [weapons, "Knife", time, "1:00"])
    terms = [weapons, "Rope", weapons, "Wrench", time, "1:00"]
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # A and B are both true => contradiction
    print(
        "White IS 2:00 and Rope IS 2:00; Either White OR Rope is 2:00 => contradiction"
    )
    apply_is(puzzle, [suspects, "White", time, "2:00"])
    apply_is(puzzle, [weapons, "Rope", time, "2:00"])
    terms = [weapons, "Rope", suspects, "White", time, "2:00"]
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete) == (True, False, True)

    terms = [suspects, "Scarlet", rooms, "Kitchen", weapons, "Knife"]
    # A is O and B is * => Set B to X
    print(
        "Scarlet has the Knife and either Scarlet OR Kitchen has the Knife => Kitchen does not have the Knife"
    )
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [suspects, "Scarlet", weapons, "Knife"])
    apply_not(puzzle, [suspects, "Scarlet", rooms, "Kitchen"])
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is O and B is X => ok
    print("Scarlet or Kitchen has the Knife; already applied")
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, True, True, set())

    # A is X and B is * => Set B to O
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "Scarlet does not have the Knife and either Scarlet OR Kitchen has the Knife => Kitchen has the Knife"
    )
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [suspects, "Scarlet", weapons, "Knife"])
    apply_not(puzzle, [suspects, "Scarlet", rooms, "Kitchen"])
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is X and B is O => ok
    print("Scarlet or Kitchen has the Knife; already applied")
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, True, True, set())

    # A is * and B is X => Set A to O
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "Kitchen does not have the Knife and either Scarlet OR Kitchen has the Knife => Scarlet has the Knife"
    )
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_not(puzzle, [rooms, "Kitchen", weapons, "Knife"])
    apply_not(puzzle, [rooms, "Kitchen", suspects, "Scarlet"])
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is * and B is O => Set A to X
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "Kitchen has the Knife and either Scarlet OR Kitchen has the Knife => Scarlet does not have the Knife"
    )
    puzzle = Puzzle([suspects, weapons, rooms, time])
    apply_is(puzzle, [rooms, "Kitchen", weapons, "Knife"])
    apply_not(puzzle, [rooms, "Kitchen", suspects, "Scarlet"])
    applied, is_valid, complete, insights = apply_simple_or(puzzle, terms)
    print(puzzle.print_grid())
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

# %%
if __name__ == "__main__":
    # Test compound or
    print("Testing compound OR")
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())
    terms = [[suspects, "White", rooms, "Kitchen"], [weapons, "Knife", time, "2:00"]]

    # No info
    print("Either White is in the Kitchen OR the Knife is at 2:00; no info")
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, True, False, set())

    # A and B are both true => contradiction
    print(
        "White IS Kitchen and Knife IS 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => contradiction"
    )
    apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
    apply_is(puzzle, [weapons, "Knife", time, "2:00"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, False, True, set())

    # A is O and B is * => Set B to X
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "White IS Kitchen; Either White is in the Kitchen OR the Knife is at 2:00 => Knife is not 2:00"
    )
    apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is O and B is X => ok
    print("Either White is in the Kitchen OR the Knife is at 2:00; already applied")
    apply_is(puzzle, [suspects, "White", rooms, "Kitchen"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (False, True, True, set())

    # A is X and B is * => Set B to O
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "White is NOT Kitchen; Either White is in the Kitchen OR the Knife is at 2:00 => Knife is 2:00"
    )
    apply_not(puzzle, [suspects, "White", rooms, "Kitchen"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is * and B is O => Set A to X
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "Knife is 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => White is not in the Kitchen"
    )
    apply_is(puzzle, [weapons, "Knife", time, "2:00"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )

    # A is * and B is X => Set A to O
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(
        "Knife is not 2:00; Either White is in the Kitchen OR the Knife is at 2:00 => White is in the Kitchen"
    )
    apply_not(puzzle, [weapons, "Knife", time, "2:00"])
    applied, is_valid, complete, insights = apply_compound_or(puzzle, terms)
    print(
        "(Applied, Is Valid, Complete, Insights): ",
        (applied, is_valid, complete, insights),
    )
    print(puzzle.print_grid())
    assert (applied, is_valid, complete, insights) == (
        True,
        True,
        True,
        {Insight.APPLY_OR},
    )


if __name__ == "__main__":
    puzzle = Puzzle([suspects, weapons, rooms, time])
    print(puzzle.print_grid())

    for i in range(30):
        hint = generate_hint(puzzle)
        print("Hint: ", str_hint(hint))
        print("(Applied, Is Valid, Complete)")
        applied, is_valid, complete, insights = apply_hint(puzzle, hint)
        print("Apply: ", (applied, is_valid, complete, insights))
        if applied:
            print("Openings: ", find_openings(puzzle))
            print("Transitives: ", find_transitives(puzzle))
        print(puzzle.print_grid())
